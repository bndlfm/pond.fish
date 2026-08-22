# -*- coding: utf-8 -*-

import asyncio
import sys
from pathlib import Path

from pond.backend.command import AgentCommand
from pond.backend.protocol import AgentRequest


FIXTURE = Path(__file__).parent / "fixtures" / "acp_timeline_agent.py"


def test_explicit_acp_turn_returns_streamed_agent_text_and_session_handle(tmp_path):
    from pond.backend.acp_client import run_acp_turn

    result = asyncio.run(run_acp_turn(
        AgentCommand((sys.executable, str(FIXTURE))),
        AgentRequest(prompt="inspect", cwd=str(tmp_path)),
    ))

    assert result.session_id == "fixture-1"
    assert result.text == "Inspecting the workspace."
    assert result.stop_reason == "end_turn"
