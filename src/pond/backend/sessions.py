"""Exact workspace/profile to ACP session handle mapping."""

import json
import os
from pathlib import Path
import tempfile

from .errors import AcpProtocolError


def normalize_workspace(path: str | Path) -> str:
    return str(Path(path).expanduser().resolve())


class SessionStore:
    """A small, atomic local pointer store; ACP owns the actual transcript."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def get(self, profile: str, workspace: str | Path) -> str | None:
        data = self._read()
        return data.get(profile, {}).get(normalize_workspace(workspace))

    def set(self, profile: str, workspace: str | Path, session_id: str) -> None:
        if not session_id:
            raise AcpProtocolError("cannot store an empty ACP session ID")
        data = self._read()
        data.setdefault(profile, {})[normalize_workspace(workspace)] = session_id
        self._write(data)

    def _read(self) -> dict[str, dict[str, str]]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AcpProtocolError("corrupt ACP session mapping") from error
        if not isinstance(data, dict):
            raise AcpProtocolError("corrupt ACP session mapping")
        return data

    def _write(self, data: dict[str, dict[str, str]]) -> None:
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.path.parent, 0o700)
        fd, temporary = tempfile.mkstemp(dir=self.path.parent, prefix=".sessions-", text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, sort_keys=True)
                handle.write("\n")
            os.chmod(temporary, 0o600)
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
