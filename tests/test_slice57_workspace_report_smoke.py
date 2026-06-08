"""Slice 57 — rapportknop en dialoog smoke."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop import messages
from rcm_desktop.adapter.report_eligibility_service import assess_report_workspace
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import (
    _ensure_app,
    _inject_run,
    _three_level_project,
)


def test_slice57_toolbar_has_report_button(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()
    assert window.generate_report_button.text() == messages.REPORT_GENERATE_BUTTON_LABEL
    assert window.generate_report_button.isEnabled() is False


def test_slice57_report_enabled_after_run(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    app.processEvents()
    assessment = assess_report_workspace(
        last_run=window._state.last_run,
        compare_slots=window._compare_slots,
        live_overlay=window.workspace_state.snapshot().planning_overlay,
    )
    assert assessment.eligible is True
    assert window.generate_report_button.isEnabled() is True
