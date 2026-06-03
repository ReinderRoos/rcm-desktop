"""Shared presentation rules for A/B compare views (slice 56)."""

from __future__ import annotations

from rcm_desktop.adapter.lcc_chart_service import LCCYearBucket


def shared_lcc_y_max(
    buckets_a: tuple[LCCYearBucket, ...],
    buckets_b: tuple[LCCYearBucket, ...],
) -> float:
    totals: list[float] = []
    for buckets in (buckets_a, buckets_b):
        for b in buckets:
            totals.append(b.correctief_eur + b.preventief_eur)
    return max(totals) if totals else 0.0


def resolve_shared_calendar_year(
    *,
    workspace_year: int | None,
    chart_a_year: int | None,
    chart_b_year: int | None,
) -> int | None:
    if workspace_year is not None:
        return workspace_year
    if chart_a_year is not None:
        return chart_a_year
    return chart_b_year
