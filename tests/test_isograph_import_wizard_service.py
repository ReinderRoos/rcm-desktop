"""Issue 06 — import wizard service (Qt-free)."""

from pathlib import Path

from rcm_core.validators import validate_project
from rcm_desktop.adapter.isograph_import_service import build_from_sheets
from rcm_desktop.adapter.isograph_import_wizard_service import (
    complete_import,
    import_from_excel,
    initial_age_conflicts,
    preview_import,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_leeg.xlsx"


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


def test_preview_reports_initial_age_conflicts() -> None:
    built = build_from_sheets(_conflict_sheets(), modeljaar=2026)
    conflicts = initial_age_conflicts(built)
    assert len(conflicts) == 1
    assert conflicts[0].pbs_id == "L2"


def test_complete_import_applies_conflict_choice() -> None:
    built = build_from_sheets(_conflict_sheets(), modeljaar=2026)
    chosen_age = 2.0
    result = complete_import(
        built, modeljaar=2026, conflict_choices={"L2": chosen_age}
    )
    assert result.project.config.modeljaar == 2026
    assert result.project.pbs_items["L2"].bouwjaar == 2024
    assert result.project.pbs_items["L1"].bouwjaar == 2024


def test_import_from_excel_fixture_without_conflicts() -> None:
    result = import_from_excel(FIXTURE, modeljaar=2026)
    assert result.project.config.modeljaar == 2026
    assert initial_age_conflicts(
        preview_import(FIXTURE, modeljaar=2026)
    ) == ()


CM_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_CM.xlsx"


def test_cm_fixture_import_valid_after_wizard_choices() -> None:
    if not CM_FIXTURE.is_file():
        return
    preview = preview_import(CM_FIXTURE, modeljaar=2026)
    choices = {c.pbs_id: c.values[0] for c in initial_age_conflicts(preview)}
    result = complete_import(
        preview, modeljaar=2026, conflict_choices=choices
    )
    assert validate_project(result.project) == []
