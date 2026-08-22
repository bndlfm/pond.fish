# -*- coding: utf-8 -*-

from pond.backend.intents import build_action_request


def test_command_draft_intent_is_explicit_and_never_authorizes_execution():
    prompt = build_action_request("command-draft", "list files modified today")

    assert "[Pond action: command-draft]" in prompt
    assert "User request: list files modified today" in prompt
    assert "Return one proposed Fish command only." in prompt
    assert "Do not execute commands or use tools." in prompt


def test_explain_intent_requests_explanation_without_command_execution():
    prompt = build_action_request("explain", "git rebase --continue")

    assert "[Pond action: explain]" in prompt
    assert "Explain the Fish command concisely." in prompt
    assert "Do not execute commands or use tools." in prompt
