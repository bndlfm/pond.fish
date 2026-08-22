# -*- coding: utf-8 -*-

from pond.backend.history import ConversationTimeline
from pond.backend.protocol import EventKind


def test_timeline_replays_terminal_activity_between_messages_without_reordering():
    timeline = ConversationTimeline()
    timeline.append_message("user", "inspect the repository")
    timeline.append_message("assistant", "I will inspect the status.")
    timeline.append_event(EventKind.TERMINAL_COMMAND, "git status --short", tool_id="term-1")
    timeline.append_event(EventKind.TERMINAL_OUTPUT, " M README.md\n", tool_id="term-1")
    timeline.append_message("assistant", "README.md has local changes.")

    replayed = ConversationTimeline.from_snapshot(timeline.snapshot())

    assert [(entry.kind, entry.text) for entry in replayed.entries] == [
        ("message", "inspect the repository"),
        ("message", "I will inspect the status."),
        ("terminal_command", "git status --short"),
        ("terminal_output", " M README.md\n"),
        ("message", "README.md has local changes."),
    ]
    assert replayed.entries[2].tool_id == "term-1"
    assert replayed.entries[3].tool_id == "term-1"


def test_timeline_records_explicit_truncation_metadata_instead_of_losing_output():
    timeline = ConversationTimeline()
    timeline.append_event(
        EventKind.TERMINAL_OUTPUT,
        "first line\n… output truncated",
        tool_id="term-1",
        original_byte_count=4096,
        truncated=True,
    )

    entry = timeline.entries[0]

    assert entry.truncated is True
    assert entry.original_byte_count == 4096


def test_terminal_events_are_only_included_when_a_later_user_turn_is_built():
    timeline = ConversationTimeline()
    timeline.append_message("assistant", "Waiting for your request.")
    timeline.append_event(EventKind.TERMINAL_COMMAND, "git status --short", tool_id="term-1")
    timeline.append_event(EventKind.TERMINAL_OUTPUT, " M README.md\n", tool_id="term-1")

    context = timeline.context_for_user_turn("Why is README modified?")

    assert [entry.kind for entry in context] == [
        "terminal_command",
        "terminal_output",
    ]
    assert [entry.text for entry in timeline.entries] == [
        "Waiting for your request.",
        "git status --short",
        " M README.md\n",
    ]
