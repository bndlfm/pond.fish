# -*- coding: utf-8 -*-

from acp.schema import UsageUpdate

from pond.backend.context import context_pressure, context_pressure_from_acp_update


def test_context_pressure_warns_at_eighty_percent_without_requesting_compaction():
    status = context_pressure(used_tokens=80_000, context_window=100_000)

    assert status.used_ratio == 0.8
    assert status.warn is True
    assert status.compact is False


def test_context_pressure_reports_harness_threshold_without_overriding_it():
    status = context_pressure(
        used_tokens=60_000,
        context_window=100_000,
        harness_threshold=0.5,
    )

    assert status.warn is False
    assert status.harness_threshold == 0.5
    assert status.compact is False


def test_context_pressure_reads_standard_acp_usage_updates():
    status = context_pressure_from_acp_update(
        UsageUpdate(used=80, size=100, session_update="usage_update")
    )

    assert status is not None
    assert status.used_ratio == 0.8
    assert status.warn is True
