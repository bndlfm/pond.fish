"""Chronological Pond conversation history independent of an ACP vendor."""

from dataclasses import asdict, dataclass
from typing import Any

from .protocol import EventKind


@dataclass(frozen=True)
class TimelineEntry:
    """One message or tool event in the order the user experienced it."""

    kind: str
    text: str
    role: str | None = None
    tool_id: str | None = None
    truncated: bool = False
    original_byte_count: int | None = None


class ConversationTimeline:
    """In-memory timeline ready for durable storage by the session layer."""

    def __init__(self) -> None:
        self.entries: list[TimelineEntry] = []

    def append_message(self, role: str, text: str) -> None:
        self.entries.append(TimelineEntry(kind="message", role=role, text=text))

    def append_event(
        self,
        kind: EventKind,
        text: str,
        *,
        tool_id: str | None = None,
        truncated: bool = False,
        original_byte_count: int | None = None,
    ) -> None:
        self.entries.append(TimelineEntry(
            kind=kind.value,
            text=text,
            tool_id=tool_id,
            truncated=truncated,
            original_byte_count=original_byte_count,
        ))

    def context_for_user_turn(self, _user_text: str) -> list[TimelineEntry]:
        """Return unseen terminal activity only when the user starts a new turn.

        Terminal observation never calls this method on its own, so command
        completion cannot wake the agent or manufacture an assistant turn.
        """
        last_user_index = max(
            (index for index, entry in enumerate(self.entries) if entry.kind == "message" and entry.role == "user"),
            default=-1,
        )
        return [
            entry for entry in self.entries[last_user_index + 1:]
            if entry.kind in {EventKind.TERMINAL_COMMAND.value, EventKind.TERMINAL_OUTPUT.value}
        ]

    def snapshot(self) -> list[dict[str, Any]]:
        return [asdict(entry) for entry in self.entries]

    @classmethod
    def from_snapshot(cls, entries: list[dict[str, Any]]) -> "ConversationTimeline":
        timeline = cls()
        timeline.entries = [TimelineEntry(**entry) for entry in entries]
        return timeline
