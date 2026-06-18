"""Slice 67 issue 01 — repair_quality import + fallback 0.0 (B1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_desktop.adapter.isograph_import_service import build_from_sheets

GAARKEUKEN = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_Gaarkeuken.rcm.json"


def _minimal_sheets(**overrides: object) -> dict:
    base = {
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
        "RcmEffects": [],
        "RcmCauseEffectAssignments": [],
        "RcmCorrectiveTasks": [
            {"Cause": "FM-A", "TaskDuration": 8, "OperationalCost": 100},
        ],
        "RcmScheduledTasks": [],
        "TaskGroups": [],
        "Project": [{"LifeTime": 876000}],
    }
    base.update(overrides)
    return base


def test_import_repair_quality_fallback_zero_when_column_absent() -> None:
    result = build_from_sheets(_minimal_sheets(), modeljaar=2026)
    assert result.project.faalwijzes["FM-A"].repair_quality == 0.0


def test_import_repair_quality_source_missing_default_0() -> None:
    result = build_from_sheets(_minimal_sheets(), modeljaar=2026)
    assert result.import_settings.get("repair_quality_source") == "missing_default_0"


def test_import_repair_quality_source_column_when_present() -> None:
    sheets = _minimal_sheets()
    sheets["RcmCorrectiveTasks"] = [
        {
            "Cause": "FM-A",
            "TaskDuration": 8,
            "OperationalCost": 100,
            "RepairQuality": 0.5,
        },
    ]
    result = build_from_sheets(sheets, modeljaar=2026)
    assert result.project.faalwijzes["FM-A"].repair_quality == pytest.approx(0.5)
    source = result.import_settings.get("repair_quality_source", "")
    assert str(source).startswith("column:")


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_gaarkeuken_fixture_repair_quality_not_all_as_new() -> None:
    from rcm_core.persistence import load_project

    project = load_project(GAARKEUKEN)
    qualities = {fm.repair_quality for fm in project.faalwijzes.values()}
    source = (project.import_settings or {}).get("repair_quality_source")
    assert qualities != {1.0} or source == "missing_default_0"
    assert any(fm.repair_quality < 0.99 for fm in project.faalwijzes.values()) or (
        source == "missing_default_0"
    )
