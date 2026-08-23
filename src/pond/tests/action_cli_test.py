# -*- coding: utf-8 -*-

import asyncio
from unittest.mock import patch

import pytest

from pond.backend.protocol import AgentResult
from pond.action_cli import run_action


def test_action_cli_creates_workspace_session_then_persists_handle(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("POND_ACP_COMMAND_JSON", '["fixture-agent"]')
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))

    async def fake_run(command, action, user_text, cwd, *, session_id=None, timeline=None):
        assert command.argv == ("fixture-agent",)
        assert action == "command-draft"
        assert user_text == "list files"
        assert session_id is None
        return AgentResult("acp-1", "ls -la", "end_turn")

    with patch("pond.action_cli.run_acp_action", fake_run), patch("pond.action_cli.hermes_server_available", return_value=False):
        run_action("command-draft", "list files", str(tmp_path), profile="default")

    assert "ls -la" in capsys.readouterr().out


def test_action_cli_reuses_exact_workspace_session_handle(tmp_path, monkeypatch):
    monkeypatch.setenv("POND_ACP_COMMAND_JSON", '["fixture-agent"]')
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    seen = []

    async def fake_run(command, action, user_text, cwd, *, session_id=None, timeline=None):
        seen.append(session_id)
        return AgentResult("acp-1", "ok", "end_turn")

    with patch("pond.action_cli.run_acp_action", fake_run), patch("pond.action_cli.hermes_server_available", return_value=False):
        run_action("agent", "ls", str(tmp_path), profile="default")
        run_action("agent", "ls", str(tmp_path), profile="default")

    assert seen == [None, "acp-1"]


def test_compress_requires_existing_workspace_session(tmp_path, monkeypatch):
    from pond.action_cli import run_compress
    from pond.backend.errors import AcpProtocolError

    monkeypatch.setenv("POND_ACP_COMMAND_JSON", '["fixture-agent"]')
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))

    with pytest.raises(AcpProtocolError, match="no ACP session"):
        run_compress(str(tmp_path), profile="default")


def test_compress_submits_slash_command_to_exact_workspace_session(tmp_path, monkeypatch):
    from pond.action_cli import run_compress
    from pond.backend.sessions import SessionStore

    monkeypatch.setenv("POND_ACP_COMMAND_JSON", '["fixture-agent"]')
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    SessionStore(tmp_path / "state" / "pond" / "acp-sessions.json").set(
        "default", tmp_path, "acp-1"
    )
    seen = []

    async def fake_turn(command, request, *, session_id=None, timeline=None):
        seen.append((request.prompt, session_id))
        return AgentResult("acp-1", "Compressed.", "end_turn")

    with patch("pond.action_cli.run_acp_turn", fake_turn):
        run_compress(str(tmp_path), profile="default")

    assert seen == [("/compress", "acp-1")]


def test_status_reports_exact_workspace_session_without_contacting_agent(tmp_path, capsys, monkeypatch):
    from pond.action_cli import run_status
    from pond.backend.sessions import SessionStore

    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    SessionStore(tmp_path / "state" / "pond" / "acp-sessions.json").set(
        "default", tmp_path, "acp-1"
    )

    run_status(str(tmp_path), profile="default")

    assert capsys.readouterr().out == "ACP session: acp-1\n"


def test_context_submits_acp_slash_command_to_exact_workspace_session(tmp_path, monkeypatch):
    from pond.action_cli import run_context
    from pond.backend.sessions import SessionStore

    monkeypatch.setenv("POND_ACP_COMMAND_JSON", '["fixture-agent"]')
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    SessionStore(tmp_path / "state" / "pond" / "acp-sessions.json").set(
        "default", tmp_path, "acp-1"
    )
    seen = []

    async def fake_turn(command, request, *, session_id=None, timeline=None):
        seen.append((request.prompt, session_id))
        return AgentResult("acp-1", "Context: 80%", "end_turn")

    with patch("pond.action_cli.run_acp_turn", fake_turn):
        run_context(str(tmp_path), profile="default")

    assert seen == [("/context", "acp-1")]
