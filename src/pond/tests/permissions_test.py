# -*- coding: utf-8 -*-

from acp.schema import PermissionOption

from pond.backend.permissions import choose_permission


def test_permission_choice_only_returns_an_option_offered_by_the_agent():
    options = [
        PermissionOption(option_id="allow_once", kind="allow_once", name="Allow once"),
        PermissionOption(option_id="deny", kind="reject_once", name="Deny"),
    ]

    assert choose_permission("y", options).option_id == "allow_once"
    assert choose_permission("a", options) is None
    assert choose_permission("n", options).option_id == "deny"


def test_turn_choice_uses_allow_once_without_inventing_an_acp_option():
    options = [
        PermissionOption(option_id="allow_once", kind="allow_once", name="Allow once"),
    ]

    choice = choose_permission("t", options)

    assert choice.option_id == "allow_once"
    assert choice.turn_scoped is True
