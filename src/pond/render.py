"""Rich-powered terminal presentation for Pond."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel


def render_markdown(text: str, *, console: Console | None = None) -> None:
    """Render markdown with Rich while allowing tests/callers to supply a console."""
    (console or Console()).print(Markdown(text or ""))


def render_tool_event(title: str, status: str, *, console: Console | None = None) -> None:
    """Render a compact chronological ACP tool lifecycle row."""
    (console or Console(stderr=True)).print(
        Panel(title, title=f"Tool · {status}", border_style="cyan")
    )
