"""Compact Rich-backed terminal presentation for Pond."""

import json
import os
import textwrap
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
    return os.environ.get("POND_FRAME_STYLE", "box") == "powerline" and os.environ.get("POND_ICON_STYLE") != "emoji"


def _box_frame_enabled() -> bool:
    return os.environ.get("POND_FRAME_STYLE", "box") == "box" and os.environ.get("POND_ICON_STYLE") != "emoji"


def _fit(text: str, width: int) -> str:
    value = Text(text)
    value.truncate(max(1, width), overflow="ellipsis")
    return value.plain


def _result_text(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("content", "text", "result_text", "output", "summary"):
            if key in value:
                return _result_text(value[key])
        return "\n".join(f"{key}: {val}" for key, val in value.items())
    if isinstance(value, list):
        return "\n".join(_result_text(item) for item in value)
    return str(value or "")


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

    def one_line(value: Any) -> str:
        return str(value).replace("\r", "\\r").replace("\n", "\\n")

    return [f"{key}: {one_line(value)}" for key, value in fields if value not in (None, "")]


def _render_framed_tool(
    target: Console,
    icon: str,
    marker: str,
    marker_style: str,
    label: str,
    detail_lines: list[str],
    result: Any,
    duration_s: float | None,
    label_style: str,
) -> None:
    max_inner = max(12, target.width - 8)
    content = [label]
    content.extend(detail_lines)
    if duration_s is not None:
        content.append(f"⏱ {duration_s:.1f}s")
    result_text = _result_text(result) if result else ""
    result_lines = result_text.strip("\\n").splitlines() or []
    if result_lines:
        content.extend(f"📋 {line}" for line in result_lines[:4])
        if len(result_lines) > 4:
            content.append(f"… output truncated ({len(result_lines) - 4} more lines)")
    inner_width = min(max_inner, max(Text(line).cell_len for line in content))
    body_prefix = "  │ "
    body_suffix = " │"
    row_width = Text(body_prefix + (" " * inner_width) + body_suffix).cell_len
    header_text = _fit(f"{icon} {marker} {label} ", inner_width)
    header = Text(f"  ╭─ {header_text}", style=label_style)
    header_suffix = "─╮"
    header.append("─" * max(0, row_width - header.cell_len - Text(header_suffix).cell_len))
    header.append(header_suffix, style=label_style)
    target.print(header, overflow="crop", no_wrap=True)
    for line in content[1:]:
        padded = _fit(line, inner_width)
        padded += " " * max(0, inner_width - Text(padded).cell_len)
        target.print(Text(f"{body_prefix}{padded}{body_suffix}"), overflow="crop", no_wrap=True)
    bottom_prefix = "  ╰─"
    bottom_suffix = "╯"
    target.print(Text(bottom_prefix + ("─" * max(0, row_width - Text(bottom_prefix + bottom_suffix).cell_len)) + bottom_suffix), overflow="crop", no_wrap=True)


def render_tool_event(
    title: str,
    status: str,
    *,
    detail: str = "",
    result: Any = "",
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
    framed = _powerline_enabled() or _box_frame_enabled()
    raw_label = f"skill: {skill}" if skill else title
    if framed:
        _render_framed_tool(
            target,
            icon,
            marker,
            marker_style,
            raw_label,
            _tool_detail(title, detail),
            result,
            duration_s,
            "magenta" if skill else "yellow",
        )
        return
    label = _fit(raw_label, max(1, target.width - 10))
    target.print(Text(f"  {icon} ", style="magenta" if skill else "yellow") + Text(marker, style=marker_style) + Text(f" {label}", style="magenta" if skill else "yellow"))
    detail_prefix = "      "
    result_prefix = "      📋 "
    for line in _tool_detail(title, detail):
        target.print(Text(_fit(f"{detail_prefix}{line}", target.width - 1)))
    if duration_s is not None:
        target.print(Text(f"{detail_prefix}⏱ {duration_s:.1f}s", style="dim"))
    if result:
        result = _result_text(result)
        source_lines = result.strip("\n").splitlines() or [""]
        rows: list[tuple[str, str]] = []
        for index, source_line in enumerate(source_lines):
            prefix = result_prefix if index == 0 else detail_prefix
            width = max(1, target.width - Text(prefix).cell_len)
            wrapped = textwrap.wrap(source_line, width=width) or [""]
            rows.extend((prefix if row_index == 0 else detail_prefix, row) for row_index, row in enumerate(wrapped))
        visible = rows[:4]
        for prefix, line in visible:
            target.print(Text(f"{prefix}{line}", style="cyan"), overflow="fold")
        if len(rows) > len(visible):
            remaining = len(rows) - len(visible)
            target.print(Text(_fit(f"{detail_prefix}… output truncated ({remaining} more rows)", target.width - 1), style="dim"))
