# -*- coding: utf-8 -*-

import io
import json
import sys
from unittest.mock import patch

import pytest

from pond import ai


def test_pond_is_the_only_supported_python_package_identity():
    import importlib.metadata
    import pond

    assert pond.__name__ == "pond"
    assert importlib.metadata.version("pond") == "3.0.0.dev0"


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


def run_ai(argv, stdin_text="", response=None):
    if response is None:
        response = {"role": "assistant", "content": "answer"}

    stdin = io.StringIO(stdin_text)
    with patch.object(sys, "argv", ["ai", *argv]), \
            patch.object(sys, "stdin", stdin), \
            patch("pond.ai.engine.get_chat_response", return_value=response) as call:
        ai.main()
    return call


def test_plain_query_preserves_prompt_words(capsys):
    call = run_ai(["explain", "this command"])

    assert capsys.readouterr().out == "answer\n"
    assert call.call_args.args[0][1] == {
        "role": "user",
        "content": "explain this command",
    }


def test_stdin_is_bounded_as_context_before_task(capsys):
    call = run_ai(["find", "errors"], "line one\nline two\n")

    assert capsys.readouterr().out == "answer\n"
    assert call.call_args.args[0][1]["content"] == (
        "Context:\nline one\nline two\n\nTask: find errors"
    )


def test_stdin_without_prompt_uses_default_task(capsys):
    call = run_ai([], "payload\n")

    assert capsys.readouterr().out == "answer\n"
    assert call.call_args.args[0][1]["content"] == (
        "Context:\npayload\n\nTask: process this input"
    )


def test_json_mode_emits_the_complete_response(capsys):
    response = {
        "role": "assistant",
        "content": "answer",
        "tool_calls": [{"id": "call-1"}],
    }

    with pytest.raises(SystemExit) as exit_info:
        run_ai(["--json", "question"], response=response)

    assert exit_info.value.code == 0
    assert json.loads(capsys.readouterr().out) == response


def test_empty_input_exits_nonzero_without_calling_backend(capsys):
    stdin = io.StringIO("")
    with patch.object(sys, "argv", ["ai"]), \
            patch.object(sys, "stdin", stdin), \
            patch("pond.ai.engine.get_chat_response") as call, \
            pytest.raises(SystemExit) as exit_info:
        ai.main()

    assert exit_info.value.code == 1
    assert "Usage:" in capsys.readouterr().out
    call.assert_not_called()


def test_backend_failure_is_stderr_and_nonzero(capsys):
    stdin = io.StringIO("")
    with patch.object(sys, "argv", ["ai", "question"]), \
            patch.object(sys, "stdin", stdin), \
            patch("pond.ai.engine.get_chat_response", side_effect=RuntimeError("offline")), \
            pytest.raises(SystemExit) as exit_info:
        ai.main()

    captured = capsys.readouterr()
    assert exit_info.value.code == 1
    assert captured.out == ""
    assert captured.err == "Error: offline\n"
