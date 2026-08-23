# -*- coding: utf-8 -*-

from io import StringIO

from rich.console import Console
from rich.text import Text

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
    assert "output truncated (1 more rows)" in output


def test_rich_renderer_caps_wrapped_long_result_rows(monkeypatch):
    monkeypatch.setenv("POND_ICON_STYLE", "emoji")
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=20)

    render_tool_event("terminal", "complete", result="x" * 200, console=console)

    output = stream.getvalue()
    assert "output tru" in output
    assert len(output.splitlines()) <= 7


def test_framed_tool_rows_share_one_right_edge(monkeypatch):
    monkeypatch.delenv("POND_ICON_STYLE", raising=False)
    monkeypatch.setenv("POND_FRAME_STYLE", "box")
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=60)

    render_tool_event("read_file", "complete", detail='{"path":"/tmp/example"}', result="short\nlonger result text", console=console)

    rows = [line for line in stream.getvalue().splitlines() if "╭" in line or "│" in line or "╰" in line]
    assert len({Text(row).cell_len for row in rows}) == 1


def test_tool_parameters_escape_newlines_to_one_line(monkeypatch):
    monkeypatch.delenv("POND_ICON_STYLE", raising=False)
    monkeypatch.setenv("POND_FRAME_STYLE", "box")
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=60)

    render_tool_event("terminal", "complete", detail='{"command":"printf \\\"a\\n b\\\""}', console=console)

    output = stream.getvalue()
    assert "\\n" in output
