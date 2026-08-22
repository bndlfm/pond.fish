"""Translate standard ACP session updates into Pond's durable timeline."""

from typing import Any

from .history import ConversationTimeline
from .protocol import EventKind


def append_acp_update(timeline: ConversationTimeline, update: Any) -> None:
    """Append an ACP update without allowing tool activity to vanish from history."""
    payload = update.model_dump(by_alias=True)
    update_kind = payload.get("sessionUpdate")

    if update_kind == "agent_message_chunk":
        content = payload.get("content") or {}
        text = content.get("text")
        if text:
            timeline.append_message("assistant", text)
        return

    if update_kind == "tool_call":
        raw_input = payload.get("rawInput") or {}
        command = raw_input.get("command") if isinstance(raw_input, dict) else None
        if command:
            timeline.append_event(
                EventKind.TERMINAL_COMMAND,
                command,
                tool_id=payload.get("toolCallId"),
            )
        return

    if update_kind == "tool_call_update":
        raw_output = payload.get("rawOutput")
        if raw_output is not None:
            text = raw_output if isinstance(raw_output, str) else str(raw_output)
            timeline.append_event(
                EventKind.TERMINAL_OUTPUT,
                text,
                tool_id=payload.get("toolCallId"),
                original_byte_count=len(text.encode()),
            )
