"""Rich-powered terminal presentation for Pond."""

from rich.console import Console
from rich.markdown import Markdown


def render_markdown(text: str, *, console: Console | None = None) -> None:
    """Render markdown with Rich while allowing tests/callers to supply a console."""
    (console or Console()).print(Markdown(text or ""))
