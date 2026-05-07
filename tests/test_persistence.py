"""Tests voor persistence.py — JSON opslaan/laden."""
import sys
import json
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.config import RCMConfig
from rcm_core.models import (
    FailureType, Faalwijze, Functie, PBSItem, PMTask, RCMProject, TaskGroup, TaskType
)
from rcm_core.persistence import load_project, save_project
from rcm_core.units import TimeDuration, TimeUnit


def _make_project() -> RCMProject:
    config = RCMConfig(lifecycle_years=80.0, modeljaar=2026)
    pbs = PBSItem("PBS-001", "Obj", "El", "BD", bouwjaar=2006, ontwerpleeftijd_jaar=40.0)
    func = Functie("FUNC-001", "PBS-001", "Draagfunctie")
    fm = Faalwijze(
        "FM-001", "PBS-001", "FUNC-001", "Corrosie",
        failure_type=FailureType.AGING, mttf_jaar=50.0, sigma_jaar=7.5,
        downtime_per_failure=TimeDuration(3.0, TimeUnit.DAYS),
        cost_cm_eur=10_000.0,
    )
    pm = PMTask(
        "PM-001", "FM-001", TaskType.IN,
        interval_jaar=2.0,
        duration=TimeDuration(8.0, TimeUnit.HOURS),
        cost_eur=600.0,
    )
    tg = TaskGroup(
        "TG-001", "Jaarlijkse ronde", TaskType.IN,
        interval_jaar=1.0,
        duration=TimeDuration(1.0, TimeUnit.DAYS),
        cost_eur=1200.0,
    )
    return RCMProject(
        config=config,
        pbs_items={"PBS-001": pbs},
        functies={"FUNC-001": func},
        faalwijzes={"FM-001": fm},
        pm_tasks={"PM-001": pm},
        task_groups={"TG-001": tg},
    )


class TestPersistence:
    def test_json_roundtrip(self, tmp_path):
        """Schrijven en teruglezen geeft identiek project."""
        project = _make_project()
        path = tmp_path / "test.rcm.json"
        save_project(project, path)
        restored = load_project(path)

        assert restored.config.lifecycle_years == 80.0
        assert "PBS-001" in restored.pbs_items
        assert "FM-001" in restored.faalwijzes
        assert restored.faalwijzes["FM-001"].failure_type == FailureType.AGING
        assert abs(restored.faalwijzes["FM-001"].mttf_jaar - 50.0) < 1e-10
        assert restored.faalwijzes["FM-001"].downtime_per_failure.unit == TimeUnit.DAYS
        assert "TG-001" in restored.task_groups

    def test_json_is_readable(self, tmp_path):
        """Opgeslagen JSON is leesbaar als standaard JSON (niet binair)."""
        project = _make_project()
        path = tmp_path / "test.rcm.json"
        save_project(project, path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "config" in data
        assert "pbs_items" in data
        assert "faalwijzes" in data

    def test_roundtrip_preserves_task_group(self, tmp_path):
        project = _make_project()
        path = tmp_path / "test.rcm.json"
        save_project(project, path)
        restored = load_project(path)
        tg = restored.task_groups["TG-001"]
        assert tg.interval_jaar == 1.0
        assert tg.duration.unit == TimeUnit.DAYS
        assert tg.cost_eur == 1200.0

    def test_load_sample_fixture(self):
        """Laad het fixture-bestand zonder fouten."""
        fixture = Path(__file__).parent / "fixtures" / "sample_project.rcm.json"
        project = load_project(fixture)
        assert len(project.pbs_items) == 4  # PBS-000 t/m PBS-003
        assert len(project.faalwijzes) == 6
        assert len(project.pm_tasks) == 8
        assert len(project.task_groups) == 1
        assert len(project.effect_klassen) == 4   # EK-SYS-01 t/m EK-SYS-04
        assert len(project.fm_effect_links) == 10  # meerdere FMs → zelfde systeem-EK
        assert len(project.pm_effect_links) == 2
