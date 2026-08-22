# -*- coding: utf-8 -*-

import pytest


def test_default_acp_command_uses_the_hermes_preset_without_shell_parsing():
    from pond.backend.command import resolve_agent_command

    command = resolve_agent_command({})

    assert command.argv == ("hermes", "acp")


def test_acp_command_accepts_an_explicit_json_argv_array():
    from pond.backend.command import resolve_agent_command

    command = resolve_agent_command({
        "POND_ACP_COMMAND_JSON": '["/opt/agent/bin/acp-agent", "--safe"]',
    })

    assert command.argv == ("/opt/agent/bin/acp-agent", "--safe")


@pytest.mark.parametrize("value", [
    '"hermes acp"',
    '[]',
    '["agent", 1]',
    '["agent", ""]',
    '["bash", "-c", "agent"]',
    'not-json',
])
def test_acp_command_rejects_ambiguous_or_shell_backed_configuration(value):
    from pond.backend.command import resolve_agent_command
    from pond.backend.errors import AgentCommandError

    with pytest.raises(AgentCommandError):
        resolve_agent_command({"POND_ACP_COMMAND_JSON": value})
