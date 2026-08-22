# -*- coding: utf-8 -*-

from io import StringIO

from rich.console import Console

from pond.render import render_markdown


def test_rich_renderer_formats_markdown_through_a_supplied_console():
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=80)

    render_markdown("# Pond\n\n`git status`", console=console)

    output = stream.getvalue()
    assert "Pond" in output
    assert "git status" in output
