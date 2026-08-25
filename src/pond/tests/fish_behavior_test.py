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


def test_pond_bind_uses_only_explicitly_configured_keys():
    script = r'''
set -gx POND_KEYMAP_CODIFY ctrl-g
set -gx POND_KEYMAP_AGENT ctrl-j
source conf.d/pond.fish
_pond_bind
bind ctrl-g
bind ctrl-j
'''
    result = run_fish(script)

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "bind -M insert ctrl-g _pond_codify_or_explain",
        "bind -M insert ctrl-j _pond_agent",
    ]


def test_pond_bind_defaults_match_fish_layout():
    result = run_fish("source conf.d/pond.fish; _pond_bind; bind ctrl-x; bind ctrl-a")

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "bind -M insert ctrl-x _pond_codify_or_explain",
        "bind -M insert ctrl-a _pond_agent",
    ]


def test_pond_stateless_query_mode_is_removed():
    result = run_fish("source functions/pond.fish; pond -q hello")

    assert result.returncode == 2
    assert "pond -q was removed" in result.stderr
def test_pond_version_reports_the_project_version_without_stderr():
    result = run_fish("source functions/pond.fish; pond version")

    assert result.returncode == 0
    assert "v3.0.0.dev3" in result.stdout
    assert result.stderr == ""


def test_pond_compress_uses_exact_acp_command_when_rewrite_is_enabled():
    script = r'''
function pond-compress
    printf 'compressed:<%s>' "$argv[2]"
end
source functions/pond.fish
pond compress
'''
    result = run_fish(script)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "compressed:<" + str(ROOT) + ">"


def test_pond_unknown_subcommand_does_not_execute_it():
    result = run_fish("source functions/pond.fish; pond definitely-not-a-command")

    assert result.returncode == 2
    assert "Unknown Pond command" in result.stderr
    assert "Use 'pond help'" in result.stderr


def test_pond_forget_clears_active_command_buffer():
    script = commandline_mock("stale command") + r'''
function pond-forget; end
source functions/pond.fish
pond forget
printf 'replacement=<%s>\n' "$__replacement"
'''
    result = run_fish(script)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "replacement=<>\n"


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
'''


def test_pond_codify_launcher_submits_stateful_command_draft():
    script = commandline_mock("# list files") + r'''
function pond-action
    printf 'stateful:%s:%s' "$argv[1]" "$argv[2]"
end
source functions/_pond_codify_or_explain.fish
_pond_codify_or_explain
printf 'replacement=<%s>\n' "$__replacement"
'''
    result = run_fish(script)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "replacement=<stateful:command-draft:# list files>\n"


def test_pond_agent_launcher_submits_stateful_goal():
    script = commandline_mock("inspect this repository") + r'''
function pond-action
    printf 'agent:%s:%s' "$argv[1]" "$argv[2]"
end
source functions/_pond_agent.fish
_pond_agent
printf 'replacement=<%s>\n' "$__replacement"
'''
    result = run_fish(script)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "agent:agent:inspect this repositoryreplacement=<>\n"
