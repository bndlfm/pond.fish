# -*- coding: utf-8 -*-

import asyncio
import sys
from pathlib import Path

from pond.backend.command import AgentCommand
from pond.backend.protocol import AgentRequest


FIXTURE = Path(__file__).parent / "fixtures" / "acp_timeline_agent.py"


def test_explicit_acp_turn_returns_streamed_agent_text_and_session_handle(tmp_path):
    from pond.backend.acp_client import run_acp_turn

    result = asyncio.run(run_acp_turn(
        AgentCommand((sys.executable, str(FIXTURE))),
        AgentRequest(prompt="inspect", cwd=str(tmp_path)),
    ))

    assert result.session_id == "fixture-1"
    assert result.text == "Inspecting the workspace."
    assert result.stop_reason == "end_turn"


def test_explicit_turn_loads_an_exact_existing_acp_session(tmp_path):
    from pond.backend.acp_client import run_acp_turn

    result = asyncio.run(run_acp_turn(
        AgentCommand((sys.executable, str(FIXTURE))),
        AgentRequest(prompt="resume", cwd=str(tmp_path)),
        session_id="fixture-restored",
    ))

    assert result.session_id == "fixture-restored"

def test_command_draft_action_uses_the_generic_acp_turn_runner(tmp_path):
    from pond.backend.acp_client import run_acp_action

    result = asyncio.run(run_acp_action(
        AgentCommand((sys.executable, str(FIXTURE))),
        "command-draft",
        "list files",
        str(tmp_path),
    ))

    assert result.session_id == "fixture-1"
    assert result.stop_reason == "end_turn"


def test_user_turn_batches_passive_terminal_entries_only_when_submitted():
    from pond.backend.acp_client import build_user_prompt
    from pond.backend.history import ConversationTimeline
    from pond.backend.protocol import EventKind

    timeline = ConversationTimeline()
    timeline.append_message("assistant", "Waiting.")
    timeline.append_event(EventKind.TERMINAL_COMMAND, "git status --short", tool_id="term-1")
    timeline.append_event(EventKind.TERMINAL_OUTPUT, " M README.md\n", tool_id="term-1")

    prompt = build_user_prompt(timeline, "Why is README modified?")

    assert prompt == (
        "[Pond explicit user turn]\n"
        "Terminal activity observed since the prior user turn:\n"
        "$ git status --short\n"
        " M README.md\n\n"
        "User request: Why is README modified?"
    )
    assert [(entry.kind, entry.text) for entry in timeline.entries] == [
        ("message", "Waiting."),
        ("terminal_command", "git status --short"),
        ("terminal_output", " M README.md\n"),
        ("message", "Why is README modified?"),
    ]
