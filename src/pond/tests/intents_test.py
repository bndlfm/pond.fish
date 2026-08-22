# -*- coding: utf-8 -*-

from pond.backend.intents import build_action_request


def test_command_draft_intent_is_explicit_and_never_authorizes_execution():
    prompt = build_action_request("command-draft", "list files modified today")

    assert "[Pond action: command-draft]" in prompt
    assert "User request: list files modified today" in prompt
    assert "Return one proposed Fish command only." in prompt
    assert "Do not execute commands or use tools." in prompt


def test_agent_intent_explicitly_authorizes_stateful_tool_work():
    prompt = build_action_request("agent", "inspect and summarize this repository")

    assert "[Pond action: agent]" in prompt
    assert "Work statefully toward the user's goal." in prompt
    assert "Use tools only when necessary and request permission when required." in prompt
