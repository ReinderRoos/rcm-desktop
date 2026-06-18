"""Slice 70 issue 11 — effect-taxonomie import."""

from __future__ import annotations

import pytest

from rcm_core.effect_taxonomy import (
    CATEGORIE_BESCHIKBAARHEID,
    CATEGORIE_OVERIG,
    CATEGORIE_VEILIGHEID,
    map_aw_effect_type,
)
from rcm_desktop.adapter.isograph_import_service import build_from_sheets


@pytest.mark.parametrize(
    ("aw_type", "expected"),
    [
        ("VGM", CATEGORIE_VEILIGHEID),
        ("Schutten", CATEGORIE_BESCHIKBAARHEID),
        ("Keren", CATEGORIE_BESCHIKBAARHEID),
    ],
)
def test_map_aw_effect_type_known(aw_type: str, expected: str) -> None:
    categorie, warn = map_aw_effect_type(aw_type)
    assert categorie == expected
    assert warn is None


def test_map_aw_effect_type_unknown() -> None:
    categorie, warn = map_aw_effect_type("OnbekendType")
    assert categorie == CATEGORIE_OVERIG
    assert warn is not None
    assert "Onbekend AW effecttype" in warn


def test_build_effect_klassen_maps_type_and_warns_on_empty() -> None:
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
        "RcmEffects": [
            {"Id": "E-VGM", "Description": "VGM", "Type": "VGM"},
            {"Id": "E-empty", "Description": "Leeg", "Type": ""},
        ],
        "RcmCauseEffectAssignments": [],
        "RcmCorrectiveTasks": [{"Cause": "FM-A", "TaskDuration": 8, "OperationalCost": 100}],
        "RcmScheduledTasks": [],
        "TaskGroups": [],
        "Project": [{"LifeTime": 876000}],
    }
    result = build_from_sheets(sheets, modeljaar=2026)
    vgm = result.project.effect_klassen["E-VGM"]
    assert vgm.categorie == CATEGORIE_VEILIGHEID
    assert vgm.aw_effect_type == "VGM"
    empty = result.project.effect_klassen["E-empty"]
    assert empty.categorie == CATEGORIE_OVERIG
    assert any("E-empty" in w and "Onbekend AW effecttype" in w for w in result.warnings)
