"""Slice 38 issue 01 — jaarklik herbouwt LCC-curve niet."""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop.adapter import lcc_planning_service
from rcm_desktop.adapter import tijdsplot_curve_service
from rcm_desktop.adapter.results_workspace_state import METRIC_KOSTEN, MODE_LCC
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import _ensure_app, _inject_run, _three_level_project


@pytest.fixture(scope="module")
def app():
    return _ensure_app()


def test_lcc_year_click_reuses_curve_without_rebuild(app, monkeypatch):
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    run = _inject_run(window, project)
    app.processEvents()

    modeljaar = int(project.config.modeljaar)
    calls = {"n": 0}
    real = lcc_planning_service.build_lcc_planning_curve_reconciled

    def counting(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(tijdsplot_curve_service, "build_lcc_planning_curve_reconciled", counting)
    window.workspace_state.set_metric(METRIC_KOSTEN)
    window.workspace_state.set_modus(MODE_LCC)
    app.processEvents()
    assert calls["n"] == 1

    window.workspace_state.set_lcc_calendar_year(modeljaar)
    app.processEvents()
    window.workspace_state.set_lcc_calendar_year(modeljaar + 1)
    app.processEvents()
    assert calls["n"] == 1
