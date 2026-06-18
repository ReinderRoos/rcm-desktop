"""Slice 108 issue 06 — FM-inspector niet zichtbaar in diagramweergave (ADR-0021)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.faalwijze_analyse_service import FM_COMPARE_VIEW_DIAGRAM
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app, _inject_run, _three_level_project
from tests.workspace_test_helpers import switch_workspace_modus


def test_fm_inspector_hidden_in_single_run_diagram(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    switch_workspace_modus(window, "fm_detail", app)
    app.processEvents()
    window.workspace_state.open_fm_inspector_mode("FM-1")
    app.processEvents()

    window._fm_bind.set_view_mode(FM_COMPARE_VIEW_DIAGRAM)
    app.processEvents()
    assert window.fm_inspector_container.isVisible() is False
    assert window.workspace_state.snapshot().fm_inspector_mode is False


def test_fm_inspector_stays_dismissed_after_render_refresh(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    switch_workspace_modus(window, "fm_detail", app)
    app.processEvents()
    window.workspace_state.open_fm_inspector_mode("FM-1")
    app.processEvents()
    window._dismiss_fm_inspector()
    app.processEvents()
    window._rerender_detail_for_current_scope()
    app.processEvents()
    assert window.workspace_state.snapshot().fm_inspector_dismissed is True
    assert window.fm_inspector_container.isVisible() is False


def test_fm_inspector_can_be_dismissed_from_table_mode(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    switch_workspace_modus(window, "fm_detail", app)
    app.processEvents()
    window.workspace_state.open_fm_inspector_mode("FM-1")
    app.processEvents()
    assert window.fm_inspector_container.isVisible() is True
    window._dismiss_fm_inspector()
    app.processEvents()
    assert window.workspace_state.snapshot().fm_inspector_dismissed is True
    assert window.fm_inspector_container.isVisible() is False


def test_fm_single_diagram_preserved_after_compare_toggle(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    switch_workspace_modus(window, "fm_detail", app)
    app.processEvents()

    window._fm_bind.set_view_mode(FM_COMPARE_VIEW_DIAGRAM)
    window.compare_toggle_button.setChecked(True)
    app.processEvents()
    window.compare_toggle_button.setChecked(False)
    app.processEvents()
    assert window._fm_bind.view_mode == FM_COMPARE_VIEW_DIAGRAM
    assert window.fm_single_diagram_view_button.isChecked() is True
