"""Client for Hermes' persistent desktop ``/api/ws`` JSON-RPC transport."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse, urlunparse

from websockets.sync.client import connect

from pond.render import render_markdown, render_thinking, render_tool_event

from .errors import AcpProtocolError
from .protocol import AgentRequest, AgentResult


def _agent_events_path() -> Path:
    configured = os.environ.get("POND_EVENTS_PATH") or os.environ.get("POND_AGENT_EVENTS_PATH")
    if configured:
        return Path(configured).expanduser()
    root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return root / "pond" / "events.jsonl"


def _record_agent_event(kind: str, session_id: str, **payload) -> None:
    path = _agent_events_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            "session_id": session_id,
            **payload,
        }
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass

def _server_url() -> str:
    return os.environ.get("POND_HERMES_SERVER_URL", "http://127.0.0.1:44437").rstrip("/")


def _desktop_token() -> str | None:
    direct = os.environ.get("POND_HERMES_WS_TOKEN") or os.environ.get("HERMES_DASHBOARD_SESSION_TOKEN")
    if direct:
        return direct
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            cmdline = (proc / "cmdline").read_bytes().replace(b"\0", b" ").decode()
            if "hermes serve" not in cmdline:
                continue
            for item in (proc / "environ").read_bytes().split(b"\0"):
                if item.startswith(b"HERMES_DASHBOARD_SESSION_TOKEN="):
                    return item.partition(b"=")[2].decode()
        except (OSError, UnicodeError):
            continue
    return None


def _ws_url() -> str:
    parsed = urlparse(_server_url())
    scheme = "wss" if parsed.scheme == "https" else "ws"
    query = dict([part.split("=", 1) for part in parsed.query.split("&") if "=" in part])
    token = _desktop_token()
    if token:
        query["token"] = token
    return urlunparse((scheme, parsed.netloc, "/api/ws", "", urlencode(query), ""))


def _rpc(ws, request_id: int, method: str, params: dict) -> dict:
    ws.send(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}))
    while True:
        frame = json.loads(ws.recv())
        if frame.get("id") == request_id:
            if "error" in frame:
                raise AcpProtocolError(str(frame["error"]))
            return frame.get("result") or {}


def hermes_server_available() -> bool:
    return bool(_desktop_token())


def run_hermes_server_turn(
    request: AgentRequest,
    session_id: str | None = None,
    *,
    suppress_activity: bool = False,
) -> AgentResult:
    """Submit one turn to the already-running Hermes desktop backend."""
    try:
        with connect(_ws_url(), open_timeout=3, close_timeout=3) as ws:
            request_id = 1
            # gateway.ready is an event, not an RPC response.
            while True:
                frame = json.loads(ws.recv())
                if frame.get("method") == "event":
                    break

            sid = ""
            if session_id and not suppress_activity:
                sid = session_id.removeprefix("hermes:")
                try:
                    _rpc(ws, request_id, "session.resume", {"session_id": sid})
                except AcpProtocolError as error:
                    if "session not found" not in str(error).lower():
                        raise
                    session_id = None
            else:
                session_id = None
            if not session_id:
                create_params = {"cols": 120, "cwd": request.cwd, "source": "pond"}
                if suppress_activity:
                    create_params["reasoning_effort"] = "none"
                result = _rpc(ws, request_id, "session.create", create_params)
                sid = result.get("session_id") or result.get("id")
                if not sid:
                    raise AcpProtocolError("Hermes server returned no session id")
            request_id += 1
            _rpc(ws, request_id, "prompt.submit", {"session_id": sid, "text": request.prompt})

            parts: list[str] = []
            thinking_parts: list[str] = []
            stop_reason = "end_turn"

            def flush_assistant_context() -> None:
                if thinking_parts:
                    if not suppress_activity:
                        render_thinking("".join(thinking_parts))
                    thinking_parts.clear()
                if parts:
                    render_markdown("".join(parts))
                    parts.clear()

            while True:
                frame = json.loads(ws.recv())
                params = frame.get("params") or {}
                if params.get("session_id") not in (None, sid):
                    continue
                event = params.get("type")
                payload = params.get("payload") or {}
                if event in {"reasoning.delta", "thinking.delta"}:
                    thinking_parts.append(str(payload.get("text") or ""))
                elif event == "message.delta":
                    parts.append(str(payload.get("text") or ""))
                elif event in {"skill.activate", "skill.start", "skill.complete"}:
                    flush_assistant_context()
                    if not suppress_activity:
                        render_tool_event(
                            "skill",
                            event.removeprefix("skill."),
                            skill=str(payload.get("name") or payload.get("skill") or "unknown"),
                            detail=str(payload.get("description") or ""),
                        )
                elif event in {"tool.start", "tool.complete", "tool.error"}:
                    flush_assistant_context()
                    if event != "tool.start" and not suppress_activity:
                        render_tool_event(
                            str(payload.get("title") or payload.get("name") or "Tool"),
                            event.removeprefix("tool."),
                            detail=json.dumps(payload.get("args") or {}, ensure_ascii=False),
                            result=payload.get("result_text") or payload.get("summary") or payload.get("result") or "",
                            duration_s=float(payload["duration_s"]) if payload.get("duration_s") is not None else None,
                        )
                elif event == "approval.request":
                    _rpc(ws, request_id + 1, "approval.respond", {"choice": "deny", "session_id": sid})
                    raise AcpProtocolError("Hermes server permission request denied by Pond fallback")
                elif event == "message.complete":
                    if thinking_parts:
                        if not suppress_activity:
                            render_thinking("".join(thinking_parts))
                        thinking_parts.clear()
                    stop_reason = str(payload.get("status") or "end_turn")
                    break
            return AgentResult(session_id=f"hermes:{sid}", text="".join(parts), stop_reason=stop_reason)
    except AcpProtocolError:
        raise
    except Exception as error:
        raise AcpProtocolError(f"Hermes server transport failed: {error}") from error
