"""Minimal stateful ACP turn runner for explicit Pond user actions."""

from __future__ import annotations

from acp import PROTOCOL_VERSION, spawn_agent_process, text_block
from acp.interfaces import Client

from .command import AgentCommand
from .errors import AcpProtocolError
from .protocol import AgentRequest, AgentResult


class _TurnClient(Client):
    def __init__(self) -> None:
        self.text_parts: list[str] = []

    async def session_update(self, session_id, update, **kwargs) -> None:
        del session_id, kwargs
        content = getattr(update, "content", None)
        text = getattr(content, "text", None)
        if text:
            self.text_parts.append(text)

    async def request_permission(self, options, session_id, tool_call, **kwargs):
        del options, session_id, tool_call, kwargs
        raise AcpProtocolError("permission requested before Pond permission UI is implemented")


async def run_acp_turn(command: AgentCommand, request: AgentRequest) -> AgentResult:
    """Run exactly one explicit user prompt through a generic ACP subprocess."""
    client = _TurnClient()
    try:
        async with spawn_agent_process(
            client,
            command.argv[0],
            *command.argv[1:],
            cwd=request.cwd,
        ) as (connection, _process):
            await connection.initialize(protocol_version=PROTOCOL_VERSION)
            session = await connection.new_session(cwd=request.cwd, mcp_servers=[])
            response = await connection.prompt(
                session_id=session.session_id,
                prompt=[text_block(request.prompt)],
            )
    except AcpProtocolError:
        raise
    except Exception as error:
        raise AcpProtocolError(f"ACP turn failed: {error}") from error

    return AgentResult(
        session_id=session.session_id,
        text="".join(client.text_parts),
        stop_reason=response.stop_reason,
    )
