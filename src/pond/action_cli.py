"""CLI bridge between Pond's Fish UI and a stateful ACP action."""

import asyncio
import os
from pathlib import Path

from .backend.acp_client import run_acp_action, run_acp_turn
from .backend.command import resolve_agent_command
from .backend.errors import AcpProtocolError
from .backend.hermes_server import hermes_server_available, run_hermes_server_turn
from .backend.intents import build_action_request
from .backend.protocol import AgentRequest
from .backend.sessions import SessionStore
from .render import render_markdown


def _state_path() -> Path:
    root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    return root / "pond" / "acp-sessions.json"


def _terminal_log_path() -> Path:
    configured = os.environ.get("FISH_COMMAND_CAPTURE_PATH")
    if configured:
        return Path(configured).expanduser()
    root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return root / "pond" / "terminal-events.jsonl"


def _pending_terminal_path() -> Path:
    root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return root / "pond" / "pending-terminal.log"


def _consume_pending_terminal() -> str:
    path = _pending_terminal_path()
    try:
        text = path.read_text(encoding="utf-8")
        path.unlink()
    except FileNotFoundError:
        return ""
    return text.strip()


def _prompt_with_terminal_context(user_text: str, explicit_context: str = "") -> str:
    pending = _consume_pending_terminal()
    context = "\n".join(part for part in (pending, explicit_context.strip()) if part)
    log_path = _terminal_log_path()
    log_hint = f"Capture log available at {log_path}. Use jq to inspect only relevant command records." if log_path.exists() else ""
    if not context and not log_hint:
        return user_text
    sections = ["[Passive terminal activity]"]
    if log_hint:
        sections.append(log_hint)
    if context:
        sections.append(context)
    sections.append(f"User request: {user_text}")
    return "\n\n".join(sections)


def run_action(action: str, user_text: str, cwd: str, *, profile: str = "default", terminal_context: str = "") -> None:
    """Run one explicit stateful action and remember its exact ACP handle."""
    user_text = _prompt_with_terminal_context(user_text, terminal_context)
    store = SessionStore(_state_path())
    session_id = store.get(profile, cwd)
    if hermes_server_available() and (not session_id or session_id.startswith("hermes:")):
        result = run_hermes_server_turn(
            AgentRequest(prompt=build_action_request(action, user_text), cwd=cwd),
            session_id=session_id,
            suppress_activity=action == "command-draft",
        )
    else:
        result = asyncio.run(run_acp_action(
            resolve_agent_command(os.environ),
            action,
            user_text,
            cwd,
            session_id=session_id,
        ))
    if action != "command-draft":
        store.set(profile, cwd, result.session_id)
    if action == "command-draft":
        print(result.text)
    else:
        render_markdown(result.text)


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
    render_markdown(result.text)


def run_status(cwd: str, *, profile: str = "default") -> None:
    """Show the exact local workspace-to-ACP-session association."""
    session_id = SessionStore(_state_path()).get(profile, cwd)
    print(f"ACP session: {session_id}" if session_id else "No ACP session is mapped to this workspace.")


def status_main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--profile", default="default")
    args = parser.parse_args()
    run_status(args.cwd, profile=args.profile)


def run_forget(cwd: str, *, profile: str = "default") -> None:
    """Detach this workspace from its ACP session without deleting agent history."""
    removed = SessionStore(_state_path()).delete(profile, cwd)
    print("Detached ACP session from this workspace." if removed else "No ACP session is mapped to this workspace.")


def forget_main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--profile", default="default")
    args = parser.parse_args()
    run_forget(args.cwd, profile=args.profile)


def run_context(cwd: str, *, profile: str = "default") -> None:
    """Ask the exact active ACP session for harness-owned context status."""
    store = SessionStore(_state_path())
    session_id = store.get(profile, cwd)
    if not session_id:
        raise AcpProtocolError("no ACP session exists for this workspace")
    result = asyncio.run(run_acp_turn(
        resolve_agent_command(os.environ),
        AgentRequest(prompt="/context", cwd=cwd),
        session_id=session_id,
    ))
    render_markdown(result.text)


def context_main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--profile", default="default")
    args = parser.parse_args()
    run_context(args.cwd, profile=args.profile)


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
    parser.add_argument("action", choices=["command-draft", "agent"])
    parser.add_argument("text")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--profile", default="default")
    parser.add_argument("--terminal-context", default="")
    args = parser.parse_args()
    run_action(args.action, args.text, args.cwd, profile=args.profile, terminal_context=args.terminal_context)


if __name__ == "__main__":
    main()
