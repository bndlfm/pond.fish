"""Safe configuration for the process Pond uses as its ACP agent."""

from dataclasses import dataclass
import json
from collections.abc import Mapping

from .errors import AgentCommandError


_DEFAULT_COMMAND = ("hermes", "acp")
_SHELL_EXECUTABLES = frozenset({"bash", "dash", "fish", "sh", "zsh"})


@dataclass(frozen=True)
class AgentCommand:
    """An argv-only command; Pond never executes this through a shell."""

    argv: tuple[str, ...]


def resolve_agent_command(environment: Mapping[str, str]) -> AgentCommand:
    """Resolve the configured ACP agent command from a JSON argv array."""
    raw = environment.get("POND_ACP_COMMAND_JSON")
    if raw is None:
        return AgentCommand(_DEFAULT_COMMAND)

    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as error:
        raise AgentCommandError("POND_ACP_COMMAND_JSON must be a JSON argv array") from error

    if not isinstance(value, list) or not value:
        raise AgentCommandError("POND_ACP_COMMAND_JSON must be a non-empty JSON argv array")
    if any(not isinstance(item, str) or not item for item in value):
        raise AgentCommandError("POND_ACP_COMMAND_JSON entries must be non-empty strings")
    if value[0] in _SHELL_EXECUTABLES:
        raise AgentCommandError("POND_ACP_COMMAND_JSON must not launch an ACP agent through a shell")

    return AgentCommand(tuple(value))
