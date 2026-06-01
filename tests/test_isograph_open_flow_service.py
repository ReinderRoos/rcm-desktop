"""Issue 08 — open RCM-Cost export: validate + atomic save (Qt-free)."""

from __future__ import annotations

from pathlib import Path

from rcm_core.persistence import load_project
from rcm_desktop.adapter.isograph_import_service import build_from_sheets
from rcm_desktop.adapter.isograph_import_wizard_service import complete_import
from rcm_desktop.adapter.isograph_open_flow_service import (
    PersistImportFailure,
    PersistImportSuccess,
    persist_import_wizard_result,
)


def _minimal_wizard_result():
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


def test_persist_import_writes_rcm_json_and_round_trips(tmp_path: Path) -> None:
    wizard = _minimal_wizard_result()
    target = tmp_path / "imported.rcm.json"

    outcome = persist_import_wizard_result(wizard, target)

    assert isinstance(outcome, PersistImportSuccess)
    assert target.is_file()
    restored = load_project(target)
    assert "FM-A" in restored.faalwijzes
    assert restored.import_settings.get("import_settings_schema_version") == 1


def test_workbook_gate_rejects_missing_must_sheet(tmp_path: Path) -> None:
    from openpyxl import Workbook

    from rcm_desktop.adapter.isograph_open_flow_service import check_workbook_importable

    path = tmp_path / "broken.xlsx"
    wb = Workbook()
    wb.save(path)

    err = check_workbook_importable(path)
    assert err is not None
    assert "tabblad" in err.message.lower() or "sheet" in err.message.lower()


def test_persist_import_returns_failure_on_validation_error(
    monkeypatch, tmp_path: Path
) -> None:
    import rcm_desktop.adapter.isograph_open_flow_service as flow
    from rcm_desktop.adapter.validate_service import ValidateResult

    wizard = _minimal_wizard_result()
    monkeypatch.setattr(
        flow,
        "validate_project_in_memory",
        lambda _p: ValidateResult(
            status="invalid",
            summary="bewust ongeldig",
            details=[],
        ),
    )

    outcome = persist_import_wizard_result(wizard, tmp_path / "bad.rcm.json")

    assert isinstance(outcome, PersistImportFailure)
    assert outcome.validate_result is not None
    assert outcome.validate_result.status == "invalid"
    assert not (tmp_path / "bad.rcm.json").exists()
