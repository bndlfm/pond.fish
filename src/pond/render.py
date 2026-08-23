"""Compact Rich-backed terminal presentation for Pond."""

import json
import os
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.text import Text


def render_markdown(text: str, *, console: Console | None = None) -> None:
    target = console or Console()
    target.print()
    target.print(Padding(Markdown(text or ""), (0, 2, 0, 2)))


_NERD_TOOL_ICONS = {
    "browser": "󰖟",
    "web": "󰖟",
    "terminal": "󰆍",
    "process": "󰒓",
    "shell": "󰆍",
    "file": "󰈙",
    "read_file": "󰈙",
    "read_files": "󰈙",
    "search_files": "󰈙",
    "patch": "󰏫",
    "write_file": "󰈔",
    "execute_code": "󰅩",
    "delegate_task": "󰘉",
    "cronjob": "󰥔",
    "memory": "󰍉",
    "todo": "󰄬",
}

_EMOJI_TOOL_ICONS = {
    "browser": "🌐",
    "web": "🌐",
    "terminal": "💻",
    "process": "⚙️",
    "shell": "💻",
    "file": "📁",
    "read_file": "📁",
    "read_files": "📁",
    "search_files": "📁",
    "patch": "📁",
    "write_file": "📁",
    "execute_code": "⚡",
    "delegate_task": "🤝",
    "cronjob": "⏰",
    "memory": "🧠",
    "todo": "✅",
}


def _tool_icon(title: str) -> str:
    icons = _EMOJI_TOOL_ICONS if os.environ.get("POND_ICON_STYLE") == "emoji" else _NERD_TOOL_ICONS
    name = title.lower()
    if name in icons:
        return icons[name]
    for group, icon in (("browser", icons["browser"]), ("web", icons["web"]), ("terminal", icons["terminal"]), ("file", icons["file"])):
        if group in name:
            return icon
    return "󰜴" if icons is _NERD_TOOL_ICONS else "🛠"


def _powerline_enabled() -> bool:
    return os.environ.get("POND_FRAME_STYLE", "powerline") == "powerline" and os.environ.get("POND_ICON_STYLE") != "emoji"


def _fit(text: str, width: int) -> str:
    value = Text(text)
    value.truncate(max(1, width), overflow="ellipsis")
    return value.plain


def _tool_detail(title: str, detail: str) -> list[str]:
    try:
        args: Any = json.loads(detail)
    except (TypeError, json.JSONDecodeError):
        return [detail.strip()] if detail.strip() else []
    if not isinstance(args, dict):
        return [str(args)]

    name = title.lower()
    if name == "search_files":
        fields = [
            ("query", args.get("pattern")),
            ("path", args.get("path")),
            ("files", args.get("file_glob")),
            ("mode", args.get("target")),
        ]
    elif name in {"read_file", "read_files"}:
        fields = [
            ("path", args.get("path") or args.get("paths")),
            ("offset", args.get("offset")),
            ("limit", args.get("limit")),
        ]
    elif name == "skill_view":
        fields = [("skill", args.get("name")), ("file", args.get("file_path"))]
    else:
        fields = list(args.items())[:4]

    return [f"{key}: {value}" for key, value in fields if value not in (None, "")]


def render_tool_event(
    title: str,
    status: str,
    *,
    detail: str = "",
    result: str = "",
    duration_s: float | None = None,
    skill: str = "",
    console: Console | None = None,
) -> None:
    """Render one dense Pond 2-style audit block, without a panel/frame."""
    target = console or Console(stderr=True)
    target.print()
    successful = status.lower() in {"complete", "completed", "success", "succeeded"}
    failed = status.lower() in {"error", "failed", "failure"}
    if successful:
        marker = "✓" if os.environ.get("POND_ICON_STYLE") == "emoji" else "󰄬"
    elif failed:
        marker = "✗" if os.environ.get("POND_ICON_STYLE") == "emoji" else "󰅖"
    else:
        marker = "•" if os.environ.get("POND_ICON_STYLE") == "emoji" else "󰔰"
    marker_style = "green" if successful else "red" if failed else "yellow"
    skill_icon = "🔌" if os.environ.get("POND_ICON_STYLE") == "emoji" else "󰏗"
    icon = skill_icon if skill else _tool_icon(title)
    label = _fit(f"skill: {skill}" if skill else title, max(12, target.width - 16))
    if _powerline_enabled():
        target.print(Text(f"   {icon} ", style="magenta" if skill else "yellow") + Text(marker, style=marker_style) + Text(f" {label} ", style="magenta" if skill else "yellow"))
        detail_prefix = "  │   "
        result_prefix = "  ╰─ 📋 "
    else:
        target.print(Text(f"  {icon} ", style="magenta" if skill else "yellow") + Text(marker, style=marker_style) + Text(f" {label}", style="magenta" if skill else "yellow"))
        detail_prefix = "      "
        result_prefix = "      📋 "
    for line in _tool_detail(title, detail):
        target.print(Text(_fit(f"{detail_prefix}{line}", target.width - 1)))
    if duration_s is not None:
        target.print(Text(f"{detail_prefix}⏱ {duration_s:.1f}s", style="dim"))
    if result:
        compact = " ".join(result.strip().splitlines())
        if len(compact) > 240:
            compact = compact[:237] + "..."
        target.print(Text(_fit(f"{result_prefix}{compact}", target.width - 1), style="cyan"))
