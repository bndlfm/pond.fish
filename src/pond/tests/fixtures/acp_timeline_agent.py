"""Deterministic standards-only ACP fixture used by Pond protocol tests."""

import asyncio
import itertools

import acp
from acp.schema import (
    Implementation,
    InitializeResponse,
    LoadSessionResponse,
    NewSessionResponse,
    PromptResponse,
    UsageUpdate,
)


class TimelineFixtureAgent:
    def __init__(self):
        self._connection = None
        self._session_ids = itertools.count(1)
        self._cancelled = set()

    def on_connect(self, connection):
        self._connection = connection

    async def initialize(self, protocol_version, **_kwargs):
        return InitializeResponse(
            protocol_version=protocol_version,
            agent_info=Implementation(name="pond-acp-fixture", version="1"),
        )

    async def new_session(self, cwd, **_kwargs):
        return NewSessionResponse(session_id=f"fixture-{next(self._session_ids)}")

    async def load_session(self, cwd, session_id, **_kwargs):
        return LoadSessionResponse()

    async def cancel(self, session_id, **_kwargs):
        self._cancelled.add(session_id)

    async def prompt(self, prompt, session_id, **_kwargs):
        if session_id in self._cancelled:
            return PromptResponse(stop_reason="cancelled")

        await self._connection.session_update(
            session_id,
            acp.update_agent_message_text("Inspecting the workspace."),
        )
        await self._connection.session_update(
            session_id,
            acp.start_tool_call(
                "terminal-1",
                "git status --short",
                kind="execute",
                status="pending",
                raw_input={"command": "git status --short"},
            ),
        )
        await self._connection.session_update(
            session_id,
            acp.update_tool_call(
                "terminal-1",
                status="completed",
                content=[acp.tool_content(acp.text_block(" M README.md\n"))],
                raw_output=" M README.md\n",
            ),
        )
        await self._connection.session_update(
            session_id,
            UsageUpdate(used=80, size=100, session_update="usage_update"),
        )
        return PromptResponse(stop_reason="end_turn")


if __name__ == "__main__":
    asyncio.run(acp.run_agent(TimelineFixtureAgent()))
