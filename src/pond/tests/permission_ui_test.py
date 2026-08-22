# -*- coding: utf-8 -*-

from io import StringIO

from acp.schema import PermissionOption

from pond.backend.permission_ui import TerminalPermissionPrompter


def test_terminal_permission_ui_renders_offered_options_and_returns_choice():
    output = StringIO()
    prompter = TerminalPermissionPrompter(reader=StringIO("y\n"), writer=output)
    options = [
        PermissionOption(option_id="allow_once", kind="allow_once", name="Allow once"),
        PermissionOption(option_id="deny", kind="reject_once", name="Deny"),
    ]

    choice = prompter.prompt("rm -rf build", "Remove build output", options)

    assert choice.option_id == "allow_once"
    assert "rm -rf build" in output.getvalue()
    assert "Allow once" in output.getvalue()


def test_terminal_permission_ui_fails_closed_on_eof():
    prompter = TerminalPermissionPrompter(reader=StringIO(""), writer=StringIO())
    options = [PermissionOption(option_id="allow_once", kind="allow_once", name="Allow once")]

    assert prompter.prompt("danger", "Dangerous command", options) is None
