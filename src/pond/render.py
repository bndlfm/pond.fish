"""Compact Rich-backed terminal presentation for Pond."""

from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text


def render_markdown(text: str, *, console: Console | None = None) -> None:
    target = console or Console()
    target.print()
    target.print(Markdown(text or ""))


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
    if skill:
        target.print(Text(f"  🔌 skill: {skill}", style="magenta"))
    target.print(Text(f"  🛠  tool: {title} [{status}]", style="yellow"))
    if detail:
        target.print(f"    {detail.strip()}")
    if result:
        compact = " ".join(result.strip().splitlines())
        if len(compact) > 240:
            compact = compact[:237] + "..."
        target.print(Text(f"    📋 result: {compact}", style="cyan"))
