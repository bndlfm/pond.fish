# -*- coding: utf-8 -*-

import asyncio
import sys
from pathlib import Path

from acp import PROTOCOL_VERSION, spawn_agent_process, text_block
from acp.interfaces import Client


FIXTURE = Path(__file__).parent / "fixtures" / "acp_timeline_agent.py"


class RecordingClient(Client):
    def __init__(self):
        self.updates = []

    async def session_update(self, session_id, update, **kwargs):
        self.updates.append((session_id, update))

    async def request_permission(self, options, session_id, tool_call, **kwargs):
        raise AssertionError("fixture should not request permission in this test")


def test_generic_acp_fixture_streams_ordered_terminal_history(tmp_path):
    async def run():
        client = RecordingClient()
        async with spawn_agent_process(
            client,
            sys.executable,
            str(FIXTURE),
            cwd=tmp_path,
        ) as (connection, _process):
            await connection.initialize(protocol_version=PROTOCOL_VERSION)
            session = await connection.new_session(cwd=str(tmp_path), mcp_servers=[])
            result = await connection.prompt(
                session_id=session.session_id,
                prompt=[text_block("inspect")],
            )
        return result, client.updates

    result, updates = asyncio.run(run())

    assert result.stop_reason == "end_turn"
    serialized = [update.model_dump(by_alias=True) for _, update in updates]
    assert serialized[1]["rawInput"] == {"command": "git status --short"}
    assert serialized[2]["rawOutput"] == " M README.md\n"
    assert len(serialized) == 4
    assert serialized[3]["sessionUpdate"] == "usage_update"

    from pond.backend.acp_events import append_acp_update
    from pond.backend.history import ConversationTimeline

    timeline = ConversationTimeline()
    timeline.append_message("user", "inspect")
    for _, update in updates:
        append_acp_update(timeline, update)
    replayed = ConversationTimeline.from_snapshot(timeline.snapshot())

    assert [(entry.kind, entry.text) for entry in replayed.entries] == [
        ("message", "inspect"),
        ("message", "Inspecting the workspace."),
        ("terminal_command", "git status --short"),
        ("terminal_output", " M README.md\n"),
    ]
