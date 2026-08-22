# -*- coding: utf-8 -*-

import asyncio
from unittest.mock import patch

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

    with patch("pond.action_cli.run_acp_action", fake_run):
        run_action("command-draft", "list files", str(tmp_path), profile="default")

    assert capsys.readouterr().out == "ls -la\n"


def test_action_cli_reuses_exact_workspace_session_handle(tmp_path, monkeypatch):
    monkeypatch.setenv("POND_ACP_COMMAND_JSON", '["fixture-agent"]')
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    seen = []

    async def fake_run(command, action, user_text, cwd, *, session_id=None, timeline=None):
        seen.append(session_id)
        return AgentResult("acp-1", "ok", "end_turn")

    with patch("pond.action_cli.run_acp_action", fake_run):
        run_action("explain", "ls", str(tmp_path), profile="default")
        run_action("explain", "ls", str(tmp_path), profile="default")

    assert seen == [None, "acp-1"]
