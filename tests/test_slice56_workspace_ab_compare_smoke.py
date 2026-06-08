"""Slice 56 issue 06 — ResultsWorkspaceWindow smoke for A/B compare."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop import messages
from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A, COMPARE_SLOT_B
from rcm_desktop.adapter.results_workspace_state import MODE_BIJDRAGEN, MODE_LCC
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import (
    _ensure_app,
    _inject_run,
    _three_level_project,
)


def test_slice56_toolbar_exposes_run_ab_seed_and_compare_toggle(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.run_slot_a_button.text() == messages.WORKSPACE_RUN_SLOT_A_BUTTON_LABEL
    assert window.run_slot_b_button.text() == messages.WORKSPACE_RUN_SLOT_B_BUTTON_LABEL
    assert window.compare_toggle_button.text() == messages.WORKSPACE_COMPARE_TOGGLE_LABEL
    assert window.compare_toggle_button.isChecked() is False
    assert window.workspace_state.snapshot().compare_mode is False


def test_slice56_seed_slot_a_with_compare_off_keeps_single_run_pane(monkeypatch) -> None:
    """Single-run UX blijft actief wanneer vergelijk-toggle uit staat."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    app.processEvents()

    window._seed_current_run_as_a()
    app.processEvents()

    assert window.compare_toggle_button.isChecked() is False
    assert window.workspace_state.snapshot().compare_mode is False
    assert window._compare_slots.has(COMPARE_SLOT_A)
    assert window.bijdragen_compare_pane.isVisible() is False
    assert window.bijdragen_single_slot_pane.isVisible() is True
    assert len(window.bijdragen_chart_widget.rows()) > 0


def test_slice56_compare_toggle_on_shows_placeholders_for_empty_slots(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    app.processEvents()

    window.compare_toggle_button.setChecked(True)
    app.processEvents()

    assert window.workspace_state.snapshot().compare_mode is True
    assert window.bijdragen_compare_pane.isVisible() is True
    assert window.bijdragen_single_slot_pane.isVisible() is False

    placeholder_a = messages.WORKSPACE_COMPARE_SLOT_PLACEHOLDER.format(slot=COMPARE_SLOT_A)
    placeholder_b = messages.WORKSPACE_COMPARE_SLOT_PLACEHOLDER.format(slot=COMPARE_SLOT_B)
    assert window._bijdragen_compare_col_a["placeholder"].text() == placeholder_a
    assert window._bijdragen_compare_col_b["placeholder"].text() == placeholder_b
    assert window._bijdragen_compare_col_a["placeholder"].isVisible() is True
    assert window._bijdragen_compare_col_b["placeholder"].isVisible() is True


def test_slice56_compare_toggle_on_lcc_modus_shows_stacked_compare_pane(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    window.workspace_state.set_modus(MODE_LCC)
    window.compare_toggle_button.setChecked(True)
    app.processEvents()

    assert window.lcc_compare_pane.isVisible() is True
    assert window.lcc_single_slot_pane.isVisible() is False


def test_slice56_clear_compare_resets_toggle_and_slots(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    window._seed_current_run_as_a()
    window.compare_toggle_button.setChecked(True)
    app.processEvents()

    window._clear_compare_slots()
    app.processEvents()

    assert window.compare_toggle_button.isChecked() is False
    assert window.workspace_state.snapshot().compare_mode is False
    assert not window._compare_slots.has(COMPARE_SLOT_A)


def test_slice56_fixture_project_path_exists() -> None:
    assert Path("tests/fixtures/sample_project.rcm.json").is_file()
