"""Issue 05 — isograph_import_service (Qt-free adapter mapper)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.models import FailureType, RCMProject, TaskType
from rcm_desktop.adapter.isograph_import_service import (
    ImportBuildResult,
    build_from_workbook,
    build_from_sheets,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_leeg.xlsx"
CM_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_CM.xlsx"
CAUSE_ID = "06H-350.1.1.1.1.1.A.1"
HOURS_PER_YEAR = 8760.0


def test_fixture_cause_maps_mttf_to_years() -> None:
    result = build_from_workbook(FIXTURE, modeljaar=2026)
    fm = result.project.faalwijzes[CAUSE_ID]
    assert fm.mttf_jaar == pytest.approx(219000 / HOURS_PER_YEAR)
    assert fm.failure_type == FailureType.AGING


def test_project_mc_fields_in_import_settings() -> None:
    result = build_from_workbook(FIXTURE, modeljaar=2026)
    assert result.import_settings["import_settings_schema_version"] == 1
    proj = result.import_settings.get("isograph_project", {})
    assert "AvsimAvailabilityPreference" in proj
    assert result.project.config.monte_carlo_n == 5000


def test_synthetic_initial_age_conflict_reported() -> None:
    sheets = {
        "RcmLocations": [
            {"Id": "L1", "Parent": "", "Description": "Loc"},
            {"Id": "L2", "Parent": "L1", "Description": "Sub"},
        ],
        "RcmFunctions": [{"Id": "F1", "Parent": "L2", "Description": "Functie"}],
        "RcmFunctionalFailures": [
            {"Id": "FF1", "Parent": "F1", "Description": "FF oms"},
        ],
        "RcmCauses": [
            {
                "Id": "FM-A",
                "Parent": "FF1",
                "Description": "FM A",
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
                "Description": "FM B",
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
        "Project": [
            {"LifeTime": 876000, "RcmNoSimulations": 100, "RcmRandomNoSeed": 7},
        ],
    }
    result = build_from_sheets(sheets, modeljaar=2026)
    assert any(c.pbs_id == "L2" and c.kind == "initial_age" for c in result.conflicts)
    assert result.project.pbs_items["L2"].bouwjaar == 0


def test_build_result_types() -> None:
    result = build_from_workbook(FIXTURE, modeljaar=2026)
    assert isinstance(result, ImportBuildResult)
    assert isinstance(result.project, RCMProject)
    assert CAUSE_ID in result.project.faalwijzes


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_cm_fixture_pm_effect_links_resolved() -> None:
    """Issue 02 spike: conservatieve PM-link resolutie op gevuld export."""
    result = build_from_workbook(CM_FIXTURE, modeljaar=2026)
    assert len(result.project.fm_effect_links) == 224
    assert len(result.project.pm_effect_links) == 54
    assert len(result.warnings) == 15
    assert all("PM-effect niet geïmporteerd" in w for w in result.warnings)
    sample = next(iter(result.project.pm_effect_links.values()))
    assert sample.fractie == 1.0
    assert sample.pm_id in result.project.pm_tasks


def test_synthetic_aw_disabled_pm_ids_in_import_settings() -> None:
    sheets = {
        "RcmLocations": [{"Id": "L1", "Parent": "", "Description": "Loc"}],
        "RcmFunctions": [{"Id": "F1", "Parent": "L1", "Description": "Functie"}],
        "RcmFunctionalFailures": [{"Id": "FF1", "Parent": "F1", "Description": "FF"}],
        "RcmCauses": [
            {
                "Id": "FM-A",
                "Parent": "FF1",
                "Description": "FM",
                "LocationId": "L1",
                "FmMttf": 87600,
                "InitialAge": 0,
                "Mttr": 8,
            },
        ],
        "RcmEffects": [{"Id": "E1", "Description": "Effect"}],
        "RcmCauseEffectAssignments": [],
        "RcmCorrectiveTasks": [{"Cause": "FM-A", "TaskDuration": 8, "OperationalCost": 100}],
        "RcmScheduledTasks": [
            {
                "Cause": "FM-A",
                "TaskId": "REV",
                "SubIndex": 0,
                "Type": "Planned",
                "Enabled": "False",
                "TaskInterval": 8760,
                "TaskDuration": 4,
            },
            {
                "Cause": "FM-A",
                "TaskId": "SVO",
                "SubIndex": 1,
                "Type": "Planned",
                "Enabled": "True",
                "TaskInterval": 8760,
                "TaskDuration": 2,
            },
        ],
        "TaskGroups": [],
        "Project": [{"LifeTime": 876000, "RcmNoSimulations": 100}],
    }
    result = build_from_sheets(sheets, modeljaar=2026)
    disabled = result.import_settings.get("aw_disabled_pm_ids", [])
    assert disabled == ["FM-A|REV|0"]
    assert "FM-A|SVO|1" not in disabled


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_cm_fixture_aw_disabled_pm_ids_populated() -> None:
    result = build_from_workbook(CM_FIXTURE, modeljaar=2026)
    disabled = result.import_settings.get("aw_disabled_pm_ids", [])
    assert len(disabled) > 0
    assert all(pm_id in result.project.pm_tasks for pm_id in disabled)
