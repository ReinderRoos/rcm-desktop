"""Slice 104 issue 02 — single-run FM table/diagram toggle."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.faalwijze_analyse_service import (
    FM_COMPARE_VIEW_DIAGRAM,
    FM_COMPARE_VIEW_TABLE,
    faalwijze_single_run_as_compare,
)
from rcm_desktop.adapter.result_view_service import FMResultRow
from rcm_desktop.adapter.results_workspace_state import METRIC_FAALMOMENTEN
from rcm_desktop.adapter.workspace_view_service import FMDetailView
from rcm_desktop.adapter.faalwijze_analyse_service import build_faalwijze_single_run_presentation
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app, _inject_run, _three_level_project
from tests.workspace_test_helpers import switch_workspace_modus


def test_single_run_as_compare_has_only_s1_values() -> None:
    view = FMDetailView(
        fm_rows=(
            FMResultRow(
                fm_id="FM-A",
                faalwijze_omschrijving="A",
                pbs_id="PBS-1",
                bouwdeel_naam="BD",
                expected_failures=42.0,
                expected_total_downtime_hr=1.0,
                total_cost_eur=100.0,
            ),
        ),
    )
    single = build_faalwijze_single_run_presentation(view, metric=METRIC_FAALMOMENTEN)
    compare = faalwijze_single_run_as_compare(single)
    assert compare.rows[0].s1 == 42.0
    assert compare.rows[0].s2 is None


def test_window_fm_single_defaults_to_table_view(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    assert window._fm_bind.view_mode == FM_COMPARE_VIEW_TABLE
    assert window.fm_single_table_view_button.isChecked()
    assert window.fm_single_chart_scroll.isVisible() is False


def test_window_fm_single_switch_to_diagram(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    switch_workspace_modus(window, "fm_detail", app)
    app.processEvents()

    assert window.fm_single_table_view_button.isVisible() is True
    window.fm_single_chart_scroll.resize(640, 480)
    window._fm_bind.set_view_mode(FM_COMPARE_VIEW_DIAGRAM)
    assert window._fm_bind.view_mode == FM_COMPARE_VIEW_DIAGRAM
    assert window.fm_single_diagram_view_button.isChecked()
    assert window.fm_single_nmf_rf_toggle.isVisible() is False
    assert len(window.fm_single_chart.fm_ids_in_order()) >= 1
