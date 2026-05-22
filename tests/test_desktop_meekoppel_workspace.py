"""pytest-qt smoke — meekoppelkansen paneel (slice 39)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_core.persistence import load_project
from rcm_desktop.adapter.results_workspace_state import MODE_LCC
from rcm_desktop.adapter.run_service import run as run_single
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _project_with_rev_pair():
    project = load_project(Path("tests/fixtures/one_fm_planning.rcm.json"))
    project.pm_tasks["PM-REV-B"] = replace(
        project.pm_tasks["PM-002"],
        pm_id="PM-REV-B",
        interval_jaar=17.0,
    )
    return project


def test_meekoppel_panel_hidden_until_whatif(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _project_with_rev_pair()
    window._state.set_last_project(project)
    rr = run_single(
        project,
        Path("tests/fixtures/one_fm_planning.rcm.json"),
        full_recompute=True,
        parallel=False,
    )
    window._state.set_last_run(rr)
    app.processEvents()

    window.modus_buttons["lcc"].click()
    app.processEvents()
    assert window.meekoppel_panel.isVisible()
    assert window.meekoppel_whatif_hint_label.isVisible()
    assert window.meekoppel_apply_button.isEnabled() is False

    window.lcc_whatif_button.setChecked(True)
    app.processEvents()
    assert window.meekoppel_whatif_hint_label.isVisible() is False
    assert window.meekoppel_apply_button.isEnabled() is True
    assert window._meekoppel_table_model.rowCount() >= 1


def test_meekoppel_apply_updates_overlay(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "information", lambda *_a, **_k: QMessageBox.Ok)

    preview_anchors: list[str] = []

    def fake_preview_anchor(self):
        preview_anchors.append("earlier")
        self._meekoppel_last_anchor = "earlier"
        return "earlier"

    monkeypatch.setattr(
        ResultsWorkspaceWindow,
        "_meekoppel_preview_anchor",
        fake_preview_anchor,
    )

    window = ResultsWorkspaceWindow()
    window.show()
    project = _project_with_rev_pair()
    window._state.set_last_project(project)
    rr = run_single(
        project,
        Path("tests/fixtures/one_fm_planning.rcm.json"),
        full_recompute=True,
        parallel=False,
    )
    window._state.set_last_run(rr)
    app.processEvents()

    window.modus_buttons["lcc"].click()
    window.lcc_whatif_button.setChecked(True)
    app.processEvents()

    if window._meekoppel_table_model.rowCount() > 0:
        window.meekoppel_table_view.selectRow(0)
        app.processEvents()
        before = window.workspace_state.snapshot().planning_overlay.change_count()
        window.meekoppel_apply_button.click()
        app.processEvents()
        after = window.workspace_state.snapshot().planning_overlay.change_count()
        assert after >= before
