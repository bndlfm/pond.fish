"""CLI bridge between Pond's Fish UI and a stateful ACP action."""

import asyncio
import os
from pathlib import Path

from .backend.acp_client import run_acp_action, run_acp_turn
from .backend.command import resolve_agent_command
from .backend.errors import AcpProtocolError
from .backend.protocol import AgentRequest
from .backend.sessions import SessionStore


def _state_path() -> Path:
    root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    return root / "pond" / "acp-sessions.json"


def run_action(action: str, user_text: str, cwd: str, *, profile: str = "default") -> None:
    """Run one explicit stateful action and remember its exact ACP handle."""
    store = SessionStore(_state_path())
    session_id = store.get(profile, cwd)
    result = asyncio.run(run_acp_action(
        resolve_agent_command(os.environ),
        action,
        user_text,
        cwd,
        session_id=session_id,
    ))
    store.set(profile, cwd, result.session_id)
    print(result.text)


def run_compress(cwd: str, *, profile: str = "default") -> None:
    """Ask the exact active ACP session to run its harness-owned compression."""
    store = SessionStore(_state_path())
    session_id = store.get(profile, cwd)
    if not session_id:
        raise AcpProtocolError("no ACP session exists for this workspace")
    result = asyncio.run(run_acp_turn(
        resolve_agent_command(os.environ),
        AgentRequest(prompt="/compress", cwd=cwd),
        session_id=session_id,
    ))
    print(result.text)


def compress_main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--profile", default="default")
    args = parser.parse_args()
    run_compress(args.cwd, profile=args.profile)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["command-draft", "explain"])
    parser.add_argument("text")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--profile", default="default")
    args = parser.parse_args()
    run_action(args.action, args.text, args.cwd, profile=args.profile)


if __name__ == "__main__":
    main()
