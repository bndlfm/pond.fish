"""Pond-owned, ACP-neutral values passed across the backend boundary."""

from dataclasses import dataclass
from enum import Enum


class EventKind(str, Enum):
    """Normalized agent lifecycle events Pond can render."""

    MESSAGE_DELTA = "message_delta"
    MESSAGE_COMPLETE = "message_complete"
    THOUGHT_DELTA = "thought_delta"
    TOOL_STARTED = "tool_started"
    TOOL_PROGRESS = "tool_progress"
    TOOL_COMPLETED = "tool_completed"
    TERMINAL_COMMAND = "terminal_command"
    TERMINAL_OUTPUT = "terminal_output"
    PERMISSION_REQUESTED = "permission_requested"
    ERROR = "error"


@dataclass(frozen=True)
class AgentRequest:
    """A stateful prompt plus the workspace it must run within."""

    prompt: str
    cwd: str


@dataclass(frozen=True)
class AgentEvent:
    """A normalized streaming event, without ACP SDK/vendor model objects."""

    kind: EventKind
    text: str = ""
    tool_id: str | None = None


@dataclass(frozen=True)
class AgentResult:
    """The final response returned after one stateful agent turn."""

    session_id: str
    text: str
    stop_reason: str
