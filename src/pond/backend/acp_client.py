"""Minimal stateful ACP turn runner for explicit Pond user actions."""

from __future__ import annotations

import json

from acp import PROTOCOL_VERSION, spawn_agent_process, text_block
from acp.interfaces import Client
from acp.schema import AllowedOutcome, RequestPermissionResponse

from pond.render import render_tool_event

from .acp_events import append_acp_update
from .command import AgentCommand
from .context import context_pressure_from_acp_update
from .errors import AcpProtocolError
from .history import ConversationTimeline
from .intents import build_action_request
from .permission_ui import TerminalPermissionPrompter
from .protocol import AgentRequest, AgentResult


class _TurnClient(Client):
    def __init__(self, timeline: ConversationTimeline | None = None) -> None:
        self.text_parts: list[str] = []
        self.context_pressure = None
        self.timeline = timeline
        self.permission_prompter = TerminalPermissionPrompter()

    async def session_update(self, session_id, update, **kwargs) -> None:
        del session_id, kwargs
        if self.timeline is not None:
            append_acp_update(self.timeline, update)
        payload = update.model_dump(by_alias=True)
        if payload.get("sessionUpdate") in {"tool_call", "tool_call_update"}:
            status = str(payload.get("status") or "running")
            if status in {"completed", "failed", "error"}:
                raw_input = payload.get("rawInput") or {}
                detail = json.dumps(raw_input, ensure_ascii=False) if raw_input else ""
                content = payload.get("content") or payload.get("output") or ""
                render_tool_event(
                    payload.get("title") or payload.get("toolCallId", "Tool"),
                    status,
                    detail=detail,
                    result=str(content) if content else "",
                )
        pressure = context_pressure_from_acp_update(update)
        if pressure is not None:
            self.context_pressure = pressure
            return
        content = getattr(update, "content", None)
        text = getattr(content, "text", None)
        if text:
            self.text_parts.append(text)

    async def request_permission(self, options, session_id, tool_call, **kwargs):
        del session_id, kwargs
        payload = tool_call.model_dump(by_alias=True)
        raw_input = payload.get("rawInput") or {}
        command = raw_input.get("command", "") if isinstance(raw_input, dict) else ""
        choice = self.permission_prompter.prompt(command, payload.get("title", ""), options)
        if choice is None:
            from acp.schema import DeniedOutcome
            return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))
        return RequestPermissionResponse(
            outcome=AllowedOutcome(option_id=choice.option_id, outcome="selected")
        )


def build_user_prompt(timeline: ConversationTimeline, user_text: str) -> str:
    """Batch passive terminal events only at an explicit user-turn boundary."""
    context = timeline.context_for_user_turn(user_text)
    lines = ["[Pond explicit user turn]"]
    if context:
        lines.append("Terminal activity observed since the prior user turn:")
        for entry in context:
            if entry.kind == "terminal_command":
                lines.append(f"$ {entry.text}")
            else:
                lines.append(entry.text.rstrip("\n"))
        lines.append("")
    lines.append(f"User request: {user_text}")
    timeline.append_message("user", user_text)
    return "\n".join(lines)


async def run_acp_action(
    command: AgentCommand,
    action: str,
    user_text: str,
    cwd: str,
    timeline: ConversationTimeline | None = None,
    session_id: str | None = None,
) -> AgentResult:
    """Submit a named Pond UI intent through the same generic ACP turn path."""
    return await run_acp_turn(
        command,
        AgentRequest(prompt=build_action_request(action, user_text), cwd=cwd),
        timeline=timeline,
        session_id=session_id,
    )


async def run_acp_turn(
    command: AgentCommand,
    request: AgentRequest,
    timeline: ConversationTimeline | None = None,
    session_id: str | None = None,
) -> AgentResult:
    """Run exactly one explicit user prompt through a generic ACP subprocess."""
    client = _TurnClient(timeline)
    try:
        async with spawn_agent_process(
            client,
            command.argv[0],
            *command.argv[1:],
            cwd=request.cwd,
        ) as (connection, _process):
            await connection.initialize(protocol_version=PROTOCOL_VERSION)
            if session_id:
                loaded = await connection.load_session(
                    cwd=request.cwd,
                    session_id=session_id,
                    mcp_servers=[],
                )
                if loaded is None:
                    raise AcpProtocolError(f"ACP session not found: {session_id}")
            else:
                session = await connection.new_session(cwd=request.cwd, mcp_servers=[])
                session_id = session.session_id
            prompt = build_user_prompt(timeline, request.prompt) if timeline else request.prompt
            response = await connection.prompt(
                session_id=session_id,
                prompt=[text_block(prompt)],
            )
    except AcpProtocolError:
        raise
    except Exception as error:
        raise AcpProtocolError(f"ACP turn failed: {error}") from error

    return AgentResult(
        session_id=session_id or "",
        text="".join(client.text_parts),
        stop_reason=response.stop_reason,
        context_pressure=client.context_pressure,
    )
