# -*- coding: utf-8 -*-

import asyncio
import os
import shutil
import subprocess

import pytest
from acp import PROTOCOL_VERSION, spawn_agent_process
from acp.interfaces import Client


class QuietClient(Client):
    async def session_update(self, session_id, update, **kwargs):
        pass

    async def request_permission(self, options, session_id, tool_call, **kwargs):
        raise AssertionError("no prompt should run in lifecycle compatibility test")


@pytest.mark.skipif(shutil.which("hermes") is None, reason="Hermes ACP is not installed")
def test_hermes_acp_self_check_passes():
    result = subprocess.run(
        ["hermes", "acp", "--check"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Hermes ACP check OK" in result.stdout


@pytest.mark.skipif(shutil.which("hermes") is None, reason="Hermes ACP is not installed")
def test_hermes_acp_supports_generic_initialize_and_cwd_bound_session(tmp_path):
    async def run():
        environment = os.environ | {"HERMES_ACP_SKIP_CONFIGURED_MCP": "1"}
        async with spawn_agent_process(
            QuietClient(),
            "hermes",
            "acp",
            cwd=tmp_path,
            env=environment,
        ) as (connection, process):
            initialized = await connection.initialize(protocol_version=PROTOCOL_VERSION)
            session = await connection.new_session(cwd=str(tmp_path), mcp_servers=[])
            return initialized, session, process.returncode

    initialized, session, returncode = asyncio.run(run())

    assert initialized.protocol_version == PROTOCOL_VERSION
    assert session.session_id
    assert returncode is None
