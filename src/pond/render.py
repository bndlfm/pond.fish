"""Compact Rich-backed terminal presentation for Pond."""

import json
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.text import Text


def render_markdown(text: str, *, console: Console | None = None) -> None:
    target = console or Console()
    target.print()
    target.print(Padding(Markdown(text or ""), (0, 2, 0, 2)))


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
    skill: str = "",
    console: Console | None = None,
) -> None:
    """Render one dense Pond 2-style audit block, without a panel/frame."""
    target = console or Console(stderr=True)
    target.print()
    successful = status.lower() in {"complete", "completed", "success", "succeeded"}
    failed = status.lower() in {"error", "failed", "failure"}
    marker = "✓" if successful else "✗" if failed else "•"
    marker_style = "green" if successful else "red" if failed else "yellow"
    if skill:
        target.print(Text(f"  🔌 skill: {skill} ", style="magenta") + Text(marker, style=marker_style))
    else:
        target.print(Text(f"  🛠  {title} ", style="yellow") + Text(marker, style=marker_style))
    for line in _tool_detail(title, detail):
        target.print(Text(f"      {line}"))
    if result:
        compact = " ".join(result.strip().splitlines())
        if len(compact) > 240:
            compact = compact[:237] + "..."
        target.print(Text(f"      📋 {compact}", style="cyan"))
