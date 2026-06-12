"""Slice 58 — pad via path_input wanneer session.path leeg is."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.views.report_generation_dialog import ReportGenerationDialog
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import (
    _ensure_app,
    _inject_run,
    _three_level_project,
)


def test_slice58_report_dialog_opens_with_path_input_only(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "information", lambda *_a, **_k: QMessageBox.Ok)

    opened: list[ReportGenerationDialog] = []
    original_init = ReportGenerationDialog.__init__

    def capturing_init(dialog_self, parent, **kwargs) -> None:
        original_init(dialog_self, parent, **kwargs)
        opened.append(dialog_self)

    monkeypatch.setattr(ReportGenerationDialog, "__init__", capturing_init)
    monkeypatch.setattr(
        ReportGenerationDialog,
        "exec",
        lambda self: __import__("PySide6.QtWidgets", fromlist=["QDialog"]).QDialog.DialogCode.Rejected,
    )

    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    project_path = Path("tests/fixtures/sample_project.rcm.json")
    window.path_input.setText(str(project_path))
    run = _inject_run(window, project)
    loaded = LoadedProject.from_core(project)
    window._state._last_project = project
    window._state._loaded_project = loaded
    window._state._last_run = run
    window._state._project_session = ProjectSession.from_parts(
        loaded,
        path=None,
        run=run,
    )
    app.processEvents()

    assert window._project_session() is not None
    assert window._project_session().path is None
    assert window._workspace_menu.actions_by_id["analysis.generate_report"].isEnabled() is True

    window._open_report_generation()
    app.processEvents()

    assert len(opened) == 1
