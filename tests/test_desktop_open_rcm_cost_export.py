"""Issue 08 — pytest-qt smoke: open RCM-Cost export → save → project in state."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pytestqt")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_desktop.adapter.isograph_import_service import build_from_sheets
from rcm_desktop.adapter.isograph_import_wizard_service import complete_import
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_leeg.xlsx"


def _valid_wizard_result():
    sheets = {
        "RcmLocations": [{"Id": "L2", "Parent": "", "Description": "Sub"}],
        "RcmFunctions": [{"Id": "F1", "Parent": "L2", "Description": "Functie"}],
        "RcmFunctionalFailures": [{"Id": "FF1", "Parent": "F1", "Description": "FF"}],
        "RcmCauses": [
            {
                "Id": "FM-A",
                "Parent": "FF1",
                "Description": "A",
                "LocationId": "L2",
                "FmMttf": 87600,
                "FmStd": 0,
                "InitialAge": 8760,
                "Mttr": 8,
                "FmDistribution": "Normal",
            },
        ],
        "RcmEffects": [{"Id": "E1", "Description": "Effect"}],
        "RcmCauseEffectAssignments": [
            {"Cause": "FM-A", "Effect": "E1", "CEnable": "True", "RedundancyFactor": 1},
        ],
        "RcmCorrectiveTasks": [
            {"Cause": "FM-A", "TaskDuration": 8, "OperationalCost": 1000},
        ],
        "RcmScheduledTasks": [],
        "TaskGroups": [],
        "Project": [{"LifeTime": 876000}],
    }
    built = build_from_sheets(sheets, modeljaar=2026)
    return complete_import(built, modeljaar=2026)


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_open_rcm_cost_export_smoke(monkeypatch, qtbot, tmp_path: Path) -> None:
    _ensure_app()
    save_path = tmp_path / "imported.rcm.json"
    wizard = _valid_wizard_result()

    monkeypatch.setattr(
        "rcm_desktop.views.results_workspace_window.check_workbook_importable",
        lambda _path: None,
    )
    monkeypatch.setattr(
        "rcm_desktop.views.results_workspace_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: (str(FIXTURE), ""),
    )
    monkeypatch.setattr(
        "rcm_desktop.views.results_workspace_window.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(save_path), ""),
    )
    monkeypatch.setattr(
        "rcm_desktop.views.results_workspace_window.run_import_wizard",
        lambda *args, **kwargs: wizard,
    )

    window = ResultsWorkspaceWindow()
    qtbot.addWidget(window)
    window._open_rcm_cost_export()

    qtbot.waitUntil(lambda: window._state.last_project is not None, timeout=3000)

    assert save_path.is_file()
    assert window.path_input.text() == str(save_path)
    assert window._state.last_result is not None
    assert window._state.last_result.status in {"valid", "valid_with_warnings"}
    assert window._state.last_project is not None
    assert window._state.last_project.functies
    assert "FM-A" in window._state.last_project.faalwijzes
