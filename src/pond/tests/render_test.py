# -*- coding: utf-8 -*-

from io import StringIO

from rich.console import Console

from pond.render import render_markdown, render_tool_event


def test_rich_renderer_formats_markdown_through_a_supplied_console():
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=80)

    render_markdown("# Pond\n\n`git status`", console=console)

    output = stream.getvalue()
    assert "Pond" in output
    assert "git status" in output


def test_rich_renderer_formats_tool_lifecycle_event():
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=80)

    render_tool_event("search_files", "complete", detail='{"pattern":"*.py","path":"src/pond"}', console=console)

    output = stream.getvalue()
    assert "🛠  search_files [complete]" in output
    assert "query: *.py" in output
    assert "path: src/pond" in output
    assert "completed" not in output
