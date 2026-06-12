"""Slice 80 issue 02 — metric-gestuurde default sortering FM-resultaten."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from rcm_desktop.adapter.fm_results_sort_policy import (
    FM_COL_DOWNTIME,
    FM_COL_FAALMOMENTEN,
    FM_COL_KOSTEN,
    default_fm_sort_column,
)
from rcm_desktop.adapter.fm_results_table_model import FMResultsSortProxy, FMResultsTableModel
from rcm_desktop.adapter.result_view_service import FMResultRow
from rcm_desktop.adapter.results_workspace_orchestrator import ResultsWorkspaceOrchestrator
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_FM_DETAIL,
    ResultsWorkspaceState,
)


def test_default_sort_column_per_metric() -> None:
    assert default_fm_sort_column(METRIC_NIET_BESCHIKBAARHEID) == FM_COL_DOWNTIME
    assert default_fm_sort_column(METRIC_FAALMOMENTEN) == FM_COL_FAALMOMENTEN
    assert default_fm_sort_column(METRIC_KOSTEN) == FM_COL_KOSTEN


def test_fm_toolbar_shows_metric_combo() -> None:
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_FM_DETAIL)
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, ws.snapshot())
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.metric_combo_visible is True


def test_fm_toolbar_shows_horizon_scale() -> None:
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_FM_DETAIL)
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, ws.snapshot())
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.horizon_lifecycle_visible is True
    assert plan.fm_toolbar.horizon_per_year_visible is True


def _row(fm_id: str, failures: float, downtime: float, cost: float) -> FMResultRow:
    return FMResultRow(
        fm_id=fm_id,
        faalwijze_omschrijving="x",
        pbs_id="PBS-1",
        bouwdeel_naam="B",
        expected_failures=failures,
        expected_total_downtime_hr=downtime,
        total_cost_eur=cost,
    )


def test_default_sort_orders_by_metric_column_descending() -> None:
    app = QApplication.instance() or QApplication([])
    del app
    rows = [
        _row("FM-LOW", 1.0, 10.0, 100.0),
        _row("FM-HIGH", 5.0, 50.0, 500.0),
    ]
    source = FMResultsTableModel(rows)
    proxy = FMResultsSortProxy()
    proxy.setSourceModel(source)
    proxy.sort(FM_COL_FAALMOMENTEN, Qt.DescendingOrder)
    ordered = [proxy.data(proxy.index(r, 0), Qt.UserRole + 1) for r in range(proxy.rowCount())]
    assert ordered == ["FM-HIGH", "FM-LOW"]
