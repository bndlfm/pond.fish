"""Permission-choice policy for Pond's future ACP terminal UI."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PermissionChoice:
    option_id: str
    turn_scoped: bool = False


_CHOICE_TO_OPTION = {
    "y": "allow_once",
    "n": "deny",
    "s": "allow_session",
    "a": "allow_always",
}


def choose_permission(key: str, options: list[Any]) -> PermissionChoice | None:
    """Select only a server-offered ACP option; unknown input fails closed."""
    offered = {option.option_id for option in options}
    normalized = key.strip().lower()
    if normalized == "t":
        return PermissionChoice("allow_once", turn_scoped=True) if "allow_once" in offered else None
    option_id = _CHOICE_TO_OPTION.get(normalized)
    if not option_id or option_id not in offered:
        return None
    return PermissionChoice(option_id)
