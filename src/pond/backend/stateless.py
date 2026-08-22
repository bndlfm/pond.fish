"""Safe opt-in contract for non-agent, stdin-to-stdout providers."""

from .command import AgentCommand
from .errors import AgentCommandError, StatelessOutputError


def resolve_stateless_command(environment: dict[str, str]) -> AgentCommand:
    """Resolve an explicit stateless provider without inventing a default."""
    raw = environment.get("POND_STATELESS_COMMAND_JSON")
    if raw is None:
        raise AgentCommandError(
            "POND_STATELESS_COMMAND_JSON is required until a safe default is proven"
        )

    # Reuse the ACP parser's argv/shell validation without accepting its default.
    from .command import resolve_agent_command
    return resolve_agent_command({"POND_ACP_COMMAND_JSON": raw})


def validate_stateless_stdout(stdout: str) -> str:
    """Keep exact output for command-buffer insertion, rejecting no response."""
    if not stdout.strip():
        raise StatelessOutputError("stateless provider returned empty stdout")
    return stdout
