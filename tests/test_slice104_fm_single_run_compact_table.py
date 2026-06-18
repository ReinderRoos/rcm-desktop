"""Slice 104 issue 01 — compact single-run FM table + metric sync."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt

from rcm_desktop.adapter.faalwijze_analyse_service import (
    build_faalwijze_single_run_presentation,
)
from rcm_desktop.adapter.fm_single_run_table_model import FMSingleRunTableModel
from rcm_desktop.adapter.result_view_service import FMResultRow
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
)
from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow
from rcm_desktop.adapter.workspace_view_service import FMDetailView
from rcm_core.simulation_engine import MetricBand
from tests.test_desktop_results_workspace_window import _ensure_app


def _analytical_row(
    fm_id: str,
    *,
    failures: float,
    cost: float = 100.0,
    downtime: float = 10.0,
    label: str = "Test",
    is_nmf: bool = False,
    rf: float = 0.0,
) -> FMResultRow:
    return FMResultRow(
        fm_id=fm_id,
        faalwijze_omschrijving=label,
        pbs_id="PBS-1",
        bouwdeel_naam="BD",
        expected_failures=failures,
        expected_total_downtime_hr=downtime,
        total_cost_eur=cost,
        is_nmf=is_nmf,
        rf=rf,
    )


def _mc_row(fm_id: str, *, failures_p50: float, cost_p50: float = 100.0) -> FMMCResultRow:
    band_f = MetricBand(p10=failures_p50, p50=failures_p50, p90=failures_p50)
    band_d = MetricBand(p10=10.0, p50=10.0, p90=10.0)
    band_c = MetricBand(p10=cost_p50, p50=cost_p50, p90=cost_p50)
    return FMMCResultRow(
        fm_id=fm_id,
        faalwijze_omschrijving=fm_id,
        bouwdeel_naam="BD",
        failures_band=band_f,
        downtime_band=band_d,
        cost_band=band_c,
        is_nmf=False,
        rf=0.0,
    )


def test_single_run_presentation_default_four_columns() -> None:
    view = FMDetailView(fm_rows=(_analytical_row("FM-A", failures=5.0),))
    pres = build_faalwijze_single_run_presentation(view, metric=METRIC_FAALMOMENTEN)
    model = FMSingleRunTableModel(pres)
    assert model.columnCount() == 4


def test_single_run_presentation_metric_switch() -> None:
    view = FMDetailView(
        fm_rows=(_analytical_row("FM-A", failures=10.0, cost=500.0, downtime=20.0),)
    )
    failures = build_faalwijze_single_run_presentation(view, metric=METRIC_FAALMOMENTEN)
    costs = build_faalwijze_single_run_presentation(view, metric=METRIC_KOSTEN)
    downtime = build_faalwijze_single_run_presentation(
        view, metric=METRIC_NIET_BESCHIKBAARHEID
    )
    assert failures.rows[0].metric_value == 10.0
    assert costs.rows[0].metric_value == 500.0
    assert downtime.rows[0].metric_value == 20.0


def test_single_run_table_hides_nmf_rf_by_default() -> None:
    view = FMDetailView(fm_rows=(_analytical_row("FM-A", failures=1.0, is_nmf=True, rf=0.5),))
    pres = build_faalwijze_single_run_presentation(view, metric=METRIC_FAALMOMENTEN)
    model = FMSingleRunTableModel(pres)
    assert model.columnCount() == 4


def test_single_run_table_shows_nmf_rf_when_enabled() -> None:
    _ensure_app()
    view = FMDetailView(fm_rows=(_analytical_row("FM-A", failures=1.0, is_nmf=True, rf=0.5),))
    pres = build_faalwijze_single_run_presentation(view, metric=METRIC_FAALMOMENTEN)
    model = FMSingleRunTableModel(pres, show_nmf_rf=True)
    assert model.columnCount() == 6


def test_single_run_mc_rows_use_p50_metric() -> None:
    view = FMDetailView(
        mc_rows=(_mc_row("FM-A", failures_p50=42.0, cost_p50=900.0),),
        is_mc_mode=True,
    )
    pres = build_faalwijze_single_run_presentation(view, metric=METRIC_FAALMOMENTEN)
    model = FMSingleRunTableModel(pres)
    metric_col = 3
    assert model.data(model.index(0, metric_col), Qt.DisplayRole) == "42"
