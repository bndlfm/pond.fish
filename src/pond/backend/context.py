"""Pond-side context-pressure display; the ACP harness owns compaction."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ContextPressure:
    used_tokens: int
    context_window: int
    used_ratio: float
    warn: bool
    compact: bool
    harness_threshold: float | None


def context_pressure(
    *,
    used_tokens: int,
    context_window: int,
    harness_threshold: float | None = None,
) -> ContextPressure:
    """Compute only a display warning; never initiate compaction from Pond."""
    ratio = used_tokens / context_window if context_window > 0 else 0.0
    return ContextPressure(
        used_tokens=used_tokens,
        context_window=context_window,
        used_ratio=ratio,
        warn=ratio >= 0.80,
        compact=False,
        harness_threshold=harness_threshold,
    )


def context_pressure_from_acp_update(update: Any) -> ContextPressure | None:
    """Read the standard ACP usage update without relying on a vendor extension."""
    payload = update.model_dump(by_alias=True)
    if payload.get("sessionUpdate") != "usage_update":
        return None
    return context_pressure(
        used_tokens=int(payload["used"]),
        context_window=int(payload["size"]),
    )
