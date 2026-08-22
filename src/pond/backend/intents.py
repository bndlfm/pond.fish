"""Pond UI intents encoded as explicit text for a single ACP protocol."""


_INSTRUCTIONS = {
    "command-draft": "Return one proposed Fish command only. Do not execute commands or use tools.",
    "agent": "Work statefully toward the user's goal. Use tools only when necessary and request permission when required.",
}


def build_action_request(action: str, user_text: str) -> str:
    """Make UI intent visible without creating a second backend protocol."""
    try:
        instructions = _INSTRUCTIONS[action]
    except KeyError as error:
        raise ValueError(f"unsupported Pond action: {action}") from error
    return (
        f"[Pond action: {action}]\n"
        f"User request: {user_text}\n\n"
        f"{instructions}"
    )
