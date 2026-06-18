"""Slice 108 issue 05 — FM-LCC plot series."""

from __future__ import annotations

from rcm_desktop.adapter.fm_lcc_plot_service import build_fm_inspector_plot_view
from rcm_desktop.adapter.fm_verification_service import (
    FMVerificationLifecycle,
    FMVerificationView,
    FMVerificationYearRow,
)
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
)


def _view(**kwargs) -> FMVerificationView:
    base = dict(
        fm_id="FM-1",
        faalwijze_omschrijving="Test",
        pbs_id="PBS-1",
        bouwdeel_naam="BD",
        fm_input_hash="abc",
        inputs=None,
        lifecycle=FMVerificationLifecycle(
            expected_failures=3.0,
            expected_raw_downtime_hr=1.0,
            expected_detection_delay_hr=0.5,
            expected_pm_downtime_hr=0.2,
            expected_total_downtime_hr=1.7,
            expected_cm_cost_eur=100.0,
            pm_cost_eur=50.0,
            total_cost_eur=150.0,
            effect_bijdragen=(),
        ),
        year_rows=(
            FMVerificationYearRow(2025, 1.0, 40.0, 0.5, 0.1, 0.6),
            FMVerificationYearRow(2026, 2.0, 60.0, 1.0, 0.2, 1.2),
        ),
        profile_missing=False,
        reconcile_ok=True,
        reconcile_notes=("OK",),
    )
    base.update(kwargs)
    return FMVerificationView(**base)


def test_kosten_plot_cm_and_pm_stacked() -> None:
    plot = build_fm_inspector_plot_view(_view(), metric=METRIC_KOSTEN)
    assert plot is not None
    assert plot.buckets[0].correctief_eur == 40.0
    assert plot.buckets[0].preventief_eur > 0
    assert plot.buckets[1].preventief_eur > plot.buckets[0].preventief_eur


def test_faalmomenten_single_series() -> None:
    plot = build_fm_inspector_plot_view(_view(), metric=METRIC_FAALMOMENTEN)
    assert plot is not None
    assert plot.buckets[0].correctief_eur == 1.0
    assert plot.buckets[0].preventief_eur == 0.0


def test_nb_uses_nb_downtime_column() -> None:
    plot = build_fm_inspector_plot_view(_view(), metric=METRIC_NIET_BESCHIKBAARHEID)
    assert plot is not None
    assert plot.buckets[0].correctief_eur == 0.6


def test_profile_missing_returns_none() -> None:
    assert build_fm_inspector_plot_view(_view(profile_missing=True, year_rows=()), metric=METRIC_KOSTEN) is None
