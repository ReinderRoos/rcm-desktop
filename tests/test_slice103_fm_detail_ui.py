"""Slice 103 — FM-resultaten UI fixes (toolbar + dubbelklik)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QDialog

from rcm_desktop import messages
from rcm_desktop.adapter.results_workspace_state import ContributionPresentation, MODE_FM_DETAIL
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import (
    _done_run_sample_fm001,
    _ensure_app,
    _inject_run,
    _three_level_project,
)
from tests.workspace_test_helpers import switch_workspace_modus


def test_fm_detail_toolbar_shows_horizon_and_year_average(monkeypatch) -> None:
    """FM-resultaten toont Per jaar + Ø per jaar (zoals Top 10), geen Uren/%."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    window.workspace_state.set_contribution_presentation(
        ContributionPresentation(horizon="per_year", year_choice="average")
    )
    switch_workspace_modus(window, "fm_detail", app)
    app.processEvents()

    assert window.horizon_lifecycle_button.isVisible()
    assert window.horizon_per_year_button.isVisible()
    assert window.contribution_year_combo.isVisible()
    assert window.contribution_year_combo.itemText(0) == messages.WORKSPACE_CONTRIBUTION_YEAR_AVERAGE
    assert window.nb_hours_button.isVisible() is False
    assert window.nb_percent_button.isVisible() is False


def test_fm_double_click_non_fm_id_column_opens_inspector(monkeypatch) -> None:
    """Dubbelklik op bouwdeel-kolom opent inspectiemodus (zelfde FM als op FM-id)."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_a, **_k: QMessageBox.Ok)

    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    window._state.set_last_run(_done_run_sample_fm001())
    switch_workspace_modus(window, "fm_detail", app)
    app.processEvents()

    model = window.fm_table_view.model()
    assert model is not None and model.rowCount() >= 1
    bouwdeel_index = model.index(0, 1)
    assert bouwdeel_index.data(Qt.DisplayRole) != "FM-001"

    window.fm_table_view.doubleClicked.emit(bouwdeel_index)
    app.processEvents()
    assert window.workspace_state.snapshot().fm_inspector_mode is True
    assert window.workspace_state.snapshot().fm_inspector_fm_id == "FM-001"


def test_fm_detail_view_toggle_visible_in_single_run(monkeypatch) -> None:
    """Tabel/diagram-wissel is zichtbaar in single-run FM-resultaten."""
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
    assert window.fm_single_diagram_view_button.isVisible() is True
    assert window.fm_compare_table_view_button.isVisible() is False
    assert window.fm_compare_diagram_view_button.isVisible() is False


def test_fm_compare_view_toggle_only_in_compare_mode(monkeypatch) -> None:
    """Tabel/diagram-wissel is alleen zichtbaar bij scenariovergelijking."""
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
    assert window.fm_single_diagram_view_button.isVisible() is True
    assert window.fm_compare_table_view_button.isVisible() is False
    assert window.fm_compare_diagram_view_button.isVisible() is False

    window.workspace_state.set_compare_mode(True)
    app.processEvents()
    assert window.fm_compare_table_view_button.isVisible() is True
    assert window.fm_compare_diagram_view_button.isVisible() is True
    assert window.fm_single_table_view_button.isVisible() is False
    assert window.fm_single_diagram_view_button.isVisible() is False
