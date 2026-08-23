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


def test_rich_renderer_formats_tool_lifecycle_event(monkeypatch):
    monkeypatch.setenv("POND_ICON_STYLE", "emoji")
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=80)

    render_tool_event("search_files", "complete", detail='{"pattern":"*.py","path":"src/pond"}', console=console)

    output = stream.getvalue()
    assert "📁 ✓ search_files" in output
    assert "✓" in output
    assert "query: *.py" in output
    assert "path: src/pond" in output
    assert "[complete]" not in output


def test_rich_renderer_preserves_four_result_lines_and_marks_truncation(monkeypatch):
    monkeypatch.setenv("POND_ICON_STYLE", "emoji")
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=80)

    render_tool_event("read_file", "complete", result="one\ntwo\nthree\nfour\nfive", console=console)

    output = stream.getvalue()
    assert "one" in output
    assert "four" in output
    assert "five" not in output
    assert "output truncated (1 more lines)" in output
