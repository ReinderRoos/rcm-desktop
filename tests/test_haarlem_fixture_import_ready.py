"""Haarlem demo-fixture: valideerbaar laden en import-klare aging-defaults (slice C)."""

from __future__ import annotations

import json
from pathlib import Path

from rcm_core.models import RCMProject
from rcm_core.validators import validate_project

HAARLEM = Path(__file__).resolve().parent / "fixtures" / "awzi_haarlem_waarderpolder_demo.rcm.json"


def _load() -> RCMProject:
    return RCMProject.from_dict(json.loads(HAARLEM.read_text(encoding="utf-8")))


def test_haarlem_fixture_validates_without_errors() -> None:
    errors = validate_project(_load())
    assert errors == []


def test_haarlem_config_has_weibull_aging_defaults_for_import() -> None:
    project = _load()
    assert project.config.default_aging_distribution == "weibull_2p"
    assert project.config.default_beta_jaar == 2.5
    assert project.projectnaam
    assert "Haarlem" in project.projectnaam


def test_haarlem_keeps_nmf_subset_with_in_tasks() -> None:
    """Zes niet-evidente FM's met IN-taak blijven als NMF-demo in het portfolio."""
    from rcm_core.models import TaskType

    project = _load()
    nmf_with_in = [
        fm.fm_id
        for fm in project.faalwijzes.values()
        if fm.is_evident is False
        and any(
            pm.fm_id == fm.fm_id and pm.taak_type == TaskType.IN
            for pm in project.pm_tasks.values()
        )
    ]
    assert sorted(nmf_with_in) == [
        "FM-027",
        "FM-029",
        "FM-031",
        "FM-033",
        "FM-048",
        "FM-061",
    ]

