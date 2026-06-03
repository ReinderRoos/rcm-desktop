from __future__ import annotations

from rcm_desktop.adapter.compare_presentation_policy import (
    resolve_shared_calendar_year,
    shared_lcc_y_max,
)
from rcm_desktop.adapter.lcc_chart_service import LCCYearBucket


def _bucket(year: int, corr: float, prev: float) -> LCCYearBucket:
    return LCCYearBucket(
        calendar_year=year,
        correctief_eur=corr,
        preventief_eur=prev,
    )


def test_shared_lcc_y_max_takes_max_over_both_series():
    a = (_bucket(2025, 100.0, 50.0),)
    b = (_bucket(2025, 200.0, 10.0),)
    assert shared_lcc_y_max(a, b) == 210.0


def test_resolve_shared_calendar_year_prefers_workspace_selection():
    year = resolve_shared_calendar_year(
        workspace_year=2028,
        chart_a_year=None,
        chart_b_year=2027,
    )
    assert year == 2028


def test_resolve_shared_calendar_year_falls_back_to_either_chart():
    year = resolve_shared_calendar_year(
        workspace_year=None,
        chart_a_year=None,
        chart_b_year=2026,
    )
    assert year == 2026
