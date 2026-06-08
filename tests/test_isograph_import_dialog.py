"""Issue 06 — import wizard dialog (pytest-qt)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_desktop.views.import_wizard_dialog import (
    ImportDialogInput,
    ImportWizardDialog,
    run_import_wizard,
)
from rcm_desktop.adapter.isograph_import_service import build_from_sheets


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _conflict_sheets() -> dict:
    return {
        "RcmLocations": [
            {"Id": "L1", "Parent": "", "Description": "Loc"},
            {"Id": "L2", "Parent": "L1", "Description": "Sub"},
        ],
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
            {
                "Id": "FM-B",
                "Parent": "FF1",
                "Description": "B",
                "LocationId": "L2",
                "FmMttf": 87600,
                "FmStd": 0,
                "InitialAge": 17520,
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


def test_wizard_dialog_sets_bouwjaar_after_conflict_choice(
    monkeypatch, tmp_path: Path,
) -> None:
    _ensure_app()
    xlsx = tmp_path / "conflict.xlsx"
    xlsx.write_bytes(b"not used")

    def fake_preview(path, *, modeljaar):
        return build_from_sheets(_conflict_sheets(), modeljaar=modeljaar)

    monkeypatch.setattr(
        "rcm_desktop.views.import_wizard_dialog.preview_import",
        fake_preview,
    )

    dialog = ImportWizardDialog(
        ImportDialogInput(path=xlsx, default_modeljaar=2026)
    )
    dialog._modeljaar_spin.setValue(2027)
    combo = dialog._choice_widgets["L2"]
    combo.setCurrentIndex(1)
    dialog._on_accept()

    result = dialog.result_value()
    assert result is not None
    assert result.project.config.modeljaar == 2027
    assert result.project.pbs_items["L2"].bouwjaar == 2025
