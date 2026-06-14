"""Slice 98 — FM table restores analytical values after MC → Analytisch switch."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop import messages
from rcm_desktop.adapter.fm_mc_results_table_model import FMMCResultsTableModel
from rcm_desktop.adapter.fm_results_table_model import FMResultsTableModel
from rcm_desktop.adapter.results_workspace_state import MODE_FM_DETAIL
from rcm_desktop.adapter.simulation_engine_service import run_monte_carlo
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import (
    _ensure_app,
    _inject_run,
    _three_level_project,
)


def _fm_source_model(window: ResultsWorkspaceWindow):
    return window._fm_table_filter_proxy.sourceModel()


def _switch_run_mode(window: ResultsWorkspaceWindow, run_mode: RunMode, app: QApplication) -> None:
    combo = window.simulation_run_mode_combo
    combo.setCurrentIndex(combo.findData(run_mode))
    app.processEvents()


def test_fm_table_switches_back_to_analytical_after_mc_mode(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    window.workspace_state.set_modus(MODE_FM_DETAIL)
    app.processEvents()

    mc = run_monte_carlo(project, n=200, seed=1)
    assert mc.status == "done"
    window._state.set_last_mc_run(mc)

    _switch_run_mode(window, RunMode.MONTE_CARLO, app)

    mc_model = _fm_source_model(window)
    assert isinstance(mc_model, FMMCResultsTableModel)
    assert "MC P50" in str(mc_model.headerData(5, Qt.Horizontal, Qt.DisplayRole))

    _switch_run_mode(window, RunMode.ANALYTICAL, app)

    fm_model = _fm_source_model(window)
    assert isinstance(fm_model, FMResultsTableModel)
    assert fm_model.rowCount() > 0
    header = str(fm_model.headerData(5, Qt.Horizontal, Qt.DisplayRole))
    assert "MC P50" not in header
    assert window.detail_empty_state_label.isVisible() is False


def test_fm_table_analytical_switch_without_run_clears_mc_model(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    mc = run_monte_carlo(project, n=200, seed=2)
    assert mc.status == "done"
    window._state.set_last_mc_run(mc)
    window.workspace_state.set_modus(MODE_FM_DETAIL)
    app.processEvents()

    _switch_run_mode(window, RunMode.MONTE_CARLO, app)
    assert isinstance(_fm_source_model(window), FMMCResultsTableModel)

    _switch_run_mode(window, RunMode.ANALYTICAL, app)

    fm_model = _fm_source_model(window)
    assert isinstance(fm_model, FMResultsTableModel)
    assert fm_model.rowCount() == 0
    assert window.detail_empty_state_label.isVisible()
    assert window.detail_empty_state_label.text() == messages.TOP10_LCC_NO_ANALYTICAL_RUN
    header = str(fm_model.headerData(5, Qt.Horizontal, Qt.DisplayRole))
    assert "MC P50" not in header


def test_fm_mc_band_tooltip_through_proxy_chain(qtbot):
    from rcm_core.simulation_engine import MetricBand
    from rcm_desktop.adapter.fm_results_table_model import FMResultsSortProxy, RAW_ROLE
    from rcm_desktop.adapter.fm_results_filter_policy import (
        FM_FILTER_BOOL_COLUMNS,
        FM_FILTER_NUMERIC_COLUMNS,
        FM_FILTER_TEXT_COLUMNS,
    )
    from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow
    from rcm_desktop.adapter.table_column_filter_proxy import TableColumnFilterProxy

    row = FMMCResultRow(
        fm_id="FM-R",
        faalwijze_omschrijving="Random",
        bouwdeel_naam="BD",
        failures_band=MetricBand(p10=1.0, p50=2.0, p90=3.0),
        downtime_band=MetricBand(p10=10.0, p50=20.0, p90=30.0),
        cost_band=MetricBand(p10=100.0, p50=200.0, p90=300.0),
        is_nmf=False,
        rf=0.5,
    )
    model = FMMCResultsTableModel([row])
    filter_proxy = TableColumnFilterProxy(
        text_columns=FM_FILTER_TEXT_COLUMNS,
        bool_columns=FM_FILTER_BOOL_COLUMNS,
        numeric_columns=FM_FILTER_NUMERIC_COLUMNS,
        raw_role=RAW_ROLE,
    )
    filter_proxy.setSourceModel(model)
    sort_proxy = FMResultsSortProxy()
    sort_proxy.setSourceModel(filter_proxy)
    tooltip = sort_proxy.data(sort_proxy.index(0, 5), Qt.ToolTipRole)
    assert tooltip is not None
    assert "P10" in tooltip and "P90" in tooltip
    assert "P50" not in tooltip
