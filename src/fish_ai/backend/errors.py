"""Pond-owned backend failures; no agent vendor types leak above this layer."""


class AgentBackendError(RuntimeError):
    """Base class for errors raised by a configured agent backend."""


class AgentCommandError(AgentBackendError):
    """The configured ACP agent command is absent or invalid."""


class AcpProtocolError(AgentBackendError):
    """The agent violated, rejected, or could not complete ACP framing."""


class AgentTimeoutError(AgentBackendError):
    """The agent did not respond before Pond's configured deadline."""


class UnsupportedCapabilityError(AgentBackendError):
    """The configured ACP agent lacks a feature Pond needs for this action."""
