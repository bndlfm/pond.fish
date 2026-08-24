# -*- coding: utf-8 -*-


def test_pond_is_the_only_supported_python_package_identity():
    import importlib.metadata
    import pond

    assert pond.__name__ == "pond"
    assert importlib.metadata.version("pond") == "3.0.0.dev1"


def test_acp_neutral_protocol_types_keep_vendor_payloads_at_the_boundary():
    from pond.backend.protocol import AgentEvent, AgentRequest, AgentResult, EventKind

    request = AgentRequest(prompt="inspect this workspace", cwd="/tmp/workspace")
    event = AgentEvent(kind=EventKind.TOOL_STARTED, tool_id="call-7", text="Read file")
    result = AgentResult(session_id="session-7", text="done", stop_reason="end_turn")

    assert request.prompt == "inspect this workspace"
    assert request.cwd == "/tmp/workspace"
    assert event.kind is EventKind.TOOL_STARTED
    assert event.tool_id == "call-7"
    assert result.session_id == "session-7"
    assert result.stop_reason == "end_turn"


def test_acp_neutral_errors_are_specific_and_do_not_depend_on_an_agent_vendor():
    from pond.backend.errors import (
        AcpProtocolError,
        AgentCommandError,
        AgentTimeoutError,
        UnsupportedCapabilityError,
    )

    assert str(AgentCommandError("agent command is missing")) == "agent command is missing"
    assert str(AcpProtocolError("bad frame")) == "bad frame"
    assert str(AgentTimeoutError("prompt timed out")) == "prompt timed out"
    assert str(UnsupportedCapabilityError("session load")) == "session load"
