# -*- coding: utf-8 -*-

import json
import os

import pytest

from pond.backend.errors import AcpProtocolError
from pond.backend.sessions import SessionStore, normalize_workspace


def test_session_store_persists_an_exact_session_per_workspace_and_profile(tmp_path):
    state_path = tmp_path / "state" / "sessions.json"
    store = SessionStore(state_path)

    store.set("default", "/tmp/workspace", "acp-session-1")
    store.set("work", "/tmp/workspace", "acp-session-2")

    reloaded = SessionStore(state_path)
    assert reloaded.get("default", "/tmp/workspace") == "acp-session-1"
    assert reloaded.get("work", "/tmp/workspace") == "acp-session-2"
    assert state_path.stat().st_mode & 0o777 == 0o600
    assert state_path.parent.stat().st_mode & 0o777 == 0o700


def test_session_store_refuses_corrupt_state_instead_of_guessing_a_session(tmp_path):
    state_path = tmp_path / "sessions.json"
    state_path.write_text("not json", encoding="utf-8")

    with pytest.raises(AcpProtocolError, match="corrupt"):
        SessionStore(state_path).get("default", "/tmp/workspace")


def test_normalize_workspace_resolves_equivalent_paths(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(workspace, target_is_directory=True)

    assert normalize_workspace(alias) == normalize_workspace(workspace)
