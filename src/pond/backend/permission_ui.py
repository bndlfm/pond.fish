"""Interactive terminal rendering for generic ACP permission requests."""

from __future__ import annotations

import sys
from typing import Any, TextIO

from .permissions import PermissionChoice, choose_permission


class TerminalPermissionPrompter:
    def __init__(self, *, reader: TextIO | None = None, writer: TextIO | None = None):
        self.reader = reader
        self.writer = writer or sys.stderr

    def prompt(self, command: str, description: str, options: list[Any]) -> PermissionChoice | None:
        writer = self.writer
        writer.write(f"\nPond agent requests permission:\n$ {command}\n")
        if description:
            writer.write(f"{description}\n")
        writer.write("Choices: " + ", ".join(option.name for option in options) + "\n")
        writer.write("Allow? [y/t/s/a/n]: ")
        writer.flush()

        if self.reader is not None:
            line = self.reader.readline()
        else:
            try:
                with open("/dev/tty", "r", encoding="utf-8") as tty:
                    line = tty.readline()
            except OSError:
                return None
        return choose_permission(line[:1], options) if line else None
