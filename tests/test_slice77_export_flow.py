"""Slice 77 issue 04 — export-flow (Qt-free) + venster smoke."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from openpyxl import Workbook
from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.isograph_export_flow_service import (
    ExportFlowBlocked,
    ExportFlowSuccess,
    export_rcm_cost_project,
)
from rcm_desktop.adapter.isograph_import_service import build_from_workbook
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import _ensure_app

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_leeg.xlsx"


def test_export_flow_blocks_without_source(tmp_path: Path) -> None:
    project = build_from_workbook(FIXTURE, modeljaar=2026).project
    outcome = export_rcm_cost_project(
        project,
        project_file_path=tmp_path / "proj.rcm.json",
        output_path=tmp_path / "out.xlsx",
    )
    assert isinstance(outcome, ExportFlowBlocked)
    assert outcome.code == "MISSING_SOURCE_WORKBOOK"


def test_export_flow_locates_missing_source(tmp_path: Path) -> None:
    project = build_from_workbook(FIXTURE, modeljaar=2026).project
    project_path = tmp_path / "proj.rcm.json"
    source = tmp_path / "bron.xlsx"
    wb = Workbook()
    wb.save(source)
    output = tmp_path / "out.xlsx"

    outcome = export_rcm_cost_project(
        project,
        project_file_path=project_path,
        output_path=output,
        located_source_path=source,
    )
    assert isinstance(outcome, ExportFlowSuccess)
    assert output.is_file()


def test_export_menu_action_exists(monkeypatch) -> None:
    _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    assert "file.export_rcm_cost" in window._workspace_menu.actions_by_id
