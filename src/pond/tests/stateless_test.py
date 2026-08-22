# -*- coding: utf-8 -*-

import pytest


def test_stateless_provider_is_opt_in_until_a_safe_default_is_proven():
    from pond.backend.errors import AgentCommandError
    from pond.backend.stateless import resolve_stateless_command

    with pytest.raises(AgentCommandError, match="POND_STATELESS_COMMAND_JSON"):
        resolve_stateless_command({})


def test_stateless_provider_requires_json_argv_and_rejects_shells():
    from pond.backend.errors import AgentCommandError
    from pond.backend.stateless import resolve_stateless_command

    command = resolve_stateless_command({
        "POND_STATELESS_COMMAND_JSON": '["/opt/provider", "--plain"]',
    })
    assert command.argv == ("/opt/provider", "--plain")

    with pytest.raises(AgentCommandError):
        resolve_stateless_command({
            "POND_STATELESS_COMMAND_JSON": '["sh", "-c", "provider"]',
        })


def test_stateless_result_rejects_empty_stdout_but_keeps_output_verbatim():
    from pond.backend.errors import StatelessOutputError
    from pond.backend.stateless import validate_stateless_stdout

    assert validate_stateless_stdout("  echo hello\n") == "  echo hello\n"
    with pytest.raises(StatelessOutputError):
        validate_stateless_stdout(" \n\t")
