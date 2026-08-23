"""Client for Hermes' persistent desktop ``/api/ws`` JSON-RPC transport."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode, urlparse, urlunparse

from websockets.sync.client import connect

from pond.render import render_tool_event

from .errors import AcpProtocolError
from .protocol import AgentRequest, AgentResult


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


def run_hermes_server_turn(request: AgentRequest, session_id: str | None = None) -> AgentResult:
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
            if session_id:
                sid = session_id.removeprefix("hermes:")
                try:
                    _rpc(ws, request_id, "session.resume", {"session_id": sid})
                except AcpProtocolError as error:
                    if "session not found" not in str(error).lower():
                        raise
                    session_id = None
            if not session_id:
                result = _rpc(ws, request_id, "session.create", {"cols": 120, "cwd": request.cwd, "source": "pond"})
                sid = result.get("session_id") or result.get("id")
                if not sid:
                    raise AcpProtocolError("Hermes server returned no session id")
            request_id += 1
            _rpc(ws, request_id, "prompt.submit", {"session_id": sid, "text": request.prompt})

            parts: list[str] = []
            stop_reason = "end_turn"
            while True:
                frame = json.loads(ws.recv())
                params = frame.get("params") or {}
                if params.get("session_id") not in (None, sid):
                    continue
                event = params.get("type")
                payload = params.get("payload") or {}
                if event == "message.delta":
                    parts.append(str(payload.get("text") or ""))
                elif event in {"tool.start", "tool.complete", "tool.error"}:
                    render_tool_event(str(payload.get("title") or payload.get("name") or "Tool"), event)
                elif event == "approval.request":
                    _rpc(ws, request_id + 1, "approval.respond", {"choice": "deny", "session_id": sid})
                    raise AcpProtocolError("Hermes server permission request denied by Pond fallback")
                elif event == "message.complete":
                    stop_reason = str(payload.get("status") or "end_turn")
                    break
            return AgentResult(session_id=f"hermes:{sid}", text="".join(parts), stop_reason=stop_reason)
    except AcpProtocolError:
        raise
    except Exception as error:
        raise AcpProtocolError(f"Hermes server transport failed: {error}") from error
