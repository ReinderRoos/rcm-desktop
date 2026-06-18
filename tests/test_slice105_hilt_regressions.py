"""Slice 105 — HILT105 NO-GO regressies (what-if, CM-filter, diagram)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_core.models import RCMProject

from rcm_desktop.adapter.results_workspace_state import METRIC_KOSTEN, MODE_FM_DETAIL
from rcm_desktop.adapter.run_service import run as run_single
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from rcm_desktop.views.widgets.faalwijze_compare_bar_chart import (
    _VALUE_FONT_POINT_SIZE,
    _VALUE_LEFT_PAD,
)

from tests.test_desktop_results_workspace_window import _ensure_app
from tests.workspace_test_helpers import switch_workspace_modus

FIXTURE = Path("tests/fixtures/one_fm_planning.rcm.json")


def _action(window: ResultsWorkspaceWindow, action_id: str):
    return window._workspace_menu.actions_by_id[action_id]


def _open_lcc_cost_with_run(window: ResultsWorkspaceWindow, monkeypatch) -> None:
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    project = RCMProject.from_dict(json.loads(FIXTURE.read_text(encoding="utf-8")))
    window._state.set_last_project(project)
    rr = run_single(project, FIXTURE, full_recompute=True, parallel=False)
    assert rr.status == "done"
    window._state.set_last_run(rr)
    window.show()
    window.workspace_state.set_active_view("output.lcc_plot")
    window.workspace_state.set_metric(METRIC_KOSTEN)
    window.workspace_state.set_lcc_whatif_collapsed_in_lcc(False)


def test_whatif_menu_toggle_works_from_fm_view(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    switch_workspace_modus(window, MODE_FM_DETAIL, app)
    app.processEvents()
    assert window.workspace_state.snapshot().modus == MODE_FM_DETAIL
    assert window.workspace_state.snapshot().planning_overlay.active is False

    _action(window, "whatif.toggle").trigger()
    app.processEvents()
    assert window.workspace_state.snapshot().planning_overlay.active is True

    _action(window, "whatif.toggle").trigger()
    app.processEvents()
    assert window.workspace_state.snapshot().planning_overlay.active is False


def test_cm_filter_checkbox_stays_visible_when_unchecked(monkeypatch) -> None:
    app = _ensure_app()
    window = ResultsWorkspaceWindow()
    _open_lcc_cost_with_run(window, monkeypatch)
    app.processEvents()

    cm_box = window._lcc_filter_checks["cm"]
    assert cm_box.isVisible() is True
    cm_box.setChecked(False)
    app.processEvents()

    assert cm_box.isVisible() is True
    assert window.workspace_state.snapshot().lcc_filters.cm is False

    cm_box.setChecked(True)
    app.processEvents()
    assert window.workspace_state.snapshot().lcc_filters.cm is True


def test_diagram_value_label_uses_larger_font_and_left_pad() -> None:
    assert _VALUE_FONT_POINT_SIZE >= 11
    assert _VALUE_LEFT_PAD >= 10
