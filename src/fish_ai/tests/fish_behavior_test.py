# -*- coding: utf-8 -*-

import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]


def run_fish(script, *, env=None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        ["fish", "--no-config", "-c", script],
        cwd=ROOT,
        env=merged_env,
        text=True,
        capture_output=True,
        check=False,
    )


def make_fake_ai(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    executable = bin_dir / "ai"
    executable.write_text(
        "#!/bin/sh\nprintf 'argc=%s' \"$#\"\nfor arg in \"$@\"; do printf '<%s>' \"$arg\"; done\nprintf '\\n'\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return tmp_path


def make_permission_requesting_agent(tmp_path, command):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    agent = bin_dir / "agent"
    agent.write_text(
        "#!/bin/sh\n"
        "action_file=''\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    --action-file) action_file=$2; shift 2 ;;\n"
        "    *) shift ;;\n"
        "  esac\n"
        "done\n"
        f"printf '%s' {command!r} > \"$action_file\"\n"
        "printf 'EXECUTE\\n'\n",
        encoding="utf-8",
    )
    agent.chmod(0o755)
    for name, body in {
        "lookup_setting": "#!/bin/sh\nexit 0\n",
        "render": "#!/bin/sh\ncat\n",
    }.items():
        executable = bin_dir / name
        executable.write_text(body, encoding="utf-8")
        executable.chmod(0o755)
    return tmp_path


def test_pond_conf_is_silent_idempotent_and_xdg_scoped(tmp_path):
    data_home = tmp_path / "data home"
    config_home = tmp_path / "config home"
    result = run_fish(
        "source conf.d/pond.fish; source conf.d/pond.fish; "
        "printf 'data=<%s> config=<%s>\\n' \"$_pond_data_dir\" \"$_pond_config_path\"",
        env={
            "XDG_DATA_HOME": str(data_home),
            "XDG_CONFIG_HOME": str(config_home),
        },
    )

    assert result.returncode == 0
    assert result.stdout == (
        f"data=<{data_home}/pond> config=<{config_home}/pond/config.ini>\n"
    )
    assert result.stderr == ""
    # Fish itself may initialize XDG_DATA_HOME/fish. Pond must not create its
    # own data/config paths merely by being sourced.
    assert not (data_home / "pond").exists()
    assert not (config_home / "pond").exists()


def test_pond_query_forwards_one_prompt_argument(tmp_path):
    install_dir = make_fake_ai(tmp_path)
    result = run_fish(
        f"set -g _fish_ai_install_dir {install_dir}; "
        "source functions/pond.fish; pond -q hello world"
    )

    assert result.returncode == 0
    assert result.stdout == "argc=1<hello world>\n"
    assert result.stderr == ""


def test_pond_json_query_forwards_json_after_prompt(tmp_path):
    install_dir = make_fake_ai(tmp_path)
    result = run_fish(
        f"set -g _fish_ai_install_dir {install_dir}; "
        "source functions/pond.fish; pond --json -q hello world"
    )

    assert result.returncode == 0
    assert result.stdout == "argc=2<hello world><--json>\n"
    assert result.stderr == ""


@pytest.mark.xfail(
    strict=True,
    reason="Pond 2.x collides with Fish's special $version variable",
)
def test_pond_version_reports_the_project_version_without_stderr():
    result = run_fish("source functions/pond.fish; pond version")

    assert result.returncode == 0
    assert "pond v2.11.1" in result.stdout
    assert result.stderr == ""


def test_pond_unknown_subcommand_does_not_execute_it():
    result = run_fish("source functions/pond.fish; pond definitely-not-a-command")

    assert result.returncode == 0
    assert "Unknown subcommand: definitely-not-a-command" in result.stdout
    assert "pond -q" in result.stdout


def commandline_mock(buffer, cursor=0):
    return f'''
set -g __buffer {subprocess.list2cmdline([buffer])}
set -g __cursor {cursor}
set -g __replacement ''
function commandline
    switch "$argv[1]"
        case --current-buffer
            printf '%s' "$__buffer"
        case --replace -r
            set -g __replacement "$argv[2]"
        case --cursor
            if test (count $argv) -gt 1
                set -g __cursor "$argv[2]"
            else
                printf '%s\\n' "$__cursor"
            end
        case -f
    end
end
function _fish_ai_show_progress_indicator; end
'''


def test_pond_codify_launcher_delegates_to_legacy_during_migration():
    script = r'''
set -g __legacy_calls 0
function _fish_ai_codify_or_explain
    set -g __legacy_calls (math $__legacy_calls + 1)
end
source functions/_pond_codify_or_explain.fish
_pond_codify_or_explain
printf 'legacy_calls=<%s>\n' "$__legacy_calls"
'''
    result = run_fish(script)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "legacy_calls=<1>\n"


def test_ctrl_q_codifies_hash_prefixed_natural_language():
    script = commandline_mock("# list files") + r'''
function _fish_ai_codify; printf 'codified:%s' "$argv[1]"; end
function _fish_ai_explain; printf 'explained:%s' "$argv[1]"; end
source functions/_fish_ai_codify_or_explain.fish
_fish_ai_codify_or_explain
printf 'replacement=<%s>\n' "$__replacement"
'''
    result = run_fish(script)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "replacement=<codified:# list files>\n"


def test_ctrl_q_explains_a_known_command():
    script = commandline_mock("printf hello") + r'''
function _fish_ai_codify; printf 'codified:%s' "$argv[1]"; end
function _fish_ai_explain; printf 'explained:%s' "$argv[1]"; end
source functions/_fish_ai_codify_or_explain.fish
_fish_ai_codify_or_explain
printf 'replacement=<%s>\n' "$__replacement"
'''
    result = run_fish(script)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "replacement=<explained:printf hello>\n"


def test_ctrl_space_replaces_buffer_and_preserves_logical_cursor():
    script = commandline_mock("echo", cursor=4) + r'''
function _fish_ai_autocomplete; printf '%s++' "$argv[1]"; end
function _fish_ai_fix; printf 'fixed:%s' "$argv[1]"; end
source functions/_fish_ai_autocomplete_or_fix.fish
_fish_ai_autocomplete_or_fix
printf 'replacement=<%s> cursor=<%s>\n' "$__replacement" "$__cursor"
'''
    result = run_fish(script)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "replacement=<echo++> cursor=<6>\n"


def test_ctrl_space_fixes_previous_command_after_failure():
    script = commandline_mock("") + r'''
function history; printf 'false --example\n'; end
function _fish_ai_autocomplete; printf 'unexpected-autocomplete'; end
function _fish_ai_fix; printf 'fixed:%s' "$argv[1]"; end
source functions/_fish_ai_autocomplete_or_fix.fish
false
_fish_ai_autocomplete_or_fix
printf 'replacement=<%s>\n' "$__replacement"
'''
    result = run_fish(script)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "replacement=<fixed:false --example>\n"


def test_agent_permission_eof_fails_closed(tmp_path):
    marker = tmp_path / "must-not-exist"
    install_dir = make_permission_requesting_agent(tmp_path / "install", f"touch {marker}")
    script = commandline_mock("create marker") + f'''
set -g _fish_ai_install_dir {install_dir}
source functions/_fish_ai_agent.fish
_fish_ai_agent
'''

    result = run_fish(script)

    assert result.returncode == 0
    assert not marker.exists()
    assert "Agent session interrupted" in result.stderr


@pytest.mark.xfail(
    strict=True,
    reason="Pond 2.x mistakes -q for a prompt when no prompt is supplied",
)
def test_pond_query_without_prompt_is_rejected(tmp_path):
    install_dir = make_fake_ai(tmp_path)
    result = run_fish(
        f"set -g _fish_ai_install_dir {install_dir}; "
        "source functions/pond.fish; pond -q"
    )

    assert result.returncode == 1
    assert "No prompt provided" in result.stdout
