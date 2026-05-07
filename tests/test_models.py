"""Tests voor models.py — dataklassen en serialisatie."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.config import RCMConfig
from rcm_core.models import (
    FailureType, Faalwijze, Functie, PBSItem, PMTask, RCMProject, TaskGroup, TaskType
)
from rcm_core.units import TimeDuration, TimeUnit


class TestPBSItem:
    def test_current_age(self):
        pbs = PBSItem("PBS-001", "Object A", "Element 1", "Bouwdeel X", bouwjaar=2006)
        assert pbs.current_age(2026) == 20.0

    def test_current_age_next_year(self):
        pbs = PBSItem("PBS-001", "Object A", "Element 1", "Bouwdeel X", bouwjaar=2006)
        assert pbs.current_age(2027) == 21.0  # automatisch bijgewerkt bij modeljaar-wijziging

    def test_current_age_zero_bouwjaar(self):
        pbs = PBSItem("PBS-001", "Object A", "Element 1", "Bouwdeel X", bouwjaar=0)
        assert pbs.current_age(2026) == 0.0

    def test_mttf_from_old(self):
        config = RCMConfig(default_mttf_multiplier=1.25)
        pbs = PBSItem("PBS-001", "Object A", "Element 1", "Bouwdeel X", ontwerpleeftijd_jaar=40.0)
        assert abs(pbs.mttf_from_old(config) - 50.0) < 1e-10

    def test_roundtrip_dict(self):
        pbs = PBSItem(
            pbs_id="PBS-001",
            object_naam="Object A",
            element_naam="Element 1",
            bouwdeel_naam="Bouwdeel X",
            multiplicity=3,
            ontwerpleeftijd_jaar=40.0,
            bouwjaar=2000,
        )
        assert PBSItem.from_dict(pbs.to_dict()) == pbs


class TestFaalwijze:
    def test_effective_sigma_default(self):
        fm = Faalwijze("FM-001", "PBS-001", "FUNC-001", "Corrosie", mttf_jaar=50.0, sigma_jaar=0.0)
        assert abs(fm.effective_sigma - 7.5) < 1e-10  # 0,15 × 50

    def test_effective_sigma_explicit(self):
        fm = Faalwijze("FM-001", "PBS-001", "FUNC-001", "Corrosie", mttf_jaar=50.0, sigma_jaar=5.0)
        assert fm.effective_sigma == 5.0

    def test_roundtrip_dict(self):
        fm = Faalwijze(
            fm_id="FM-001",
            pbs_id="PBS-001",
            functie_id="FUNC-001",
            faalwijze_omschrijving="Corrosie",
            failure_type=FailureType.AGING,
            mttf_jaar=50.0,
            sigma_jaar=7.5,
            repair_quality=0.8,
            is_evident=False,
            p_ongewenste_gebeurtenis=0.6,
            downtime_per_failure=TimeDuration(3.0, TimeUnit.DAYS),
            cost_cm_eur=5000.0,
        )
        restored = Faalwijze.from_dict(fm.to_dict())
        assert restored.fm_id == fm.fm_id
        assert restored.failure_type == FailureType.AGING
        assert restored.downtime_per_failure.unit == TimeUnit.DAYS
        assert abs(restored.downtime_per_failure.value - 3.0) < 1e-10


class TestPMTask:
    def test_roundtrip_dict(self):
        task = PMTask(
            pm_id="PM-001",
            fm_id="FM-001",
            taak_type=TaskType.IN,
            interval_jaar=1.0,
            duration=TimeDuration(8.0, TimeUnit.HOURS),
            cost_eur=500.0,
            causes_unavailability=True,
            unavailability_fraction=0.5,
        )
        restored = PMTask.from_dict(task.to_dict())
        assert restored.taak_type == TaskType.IN
        assert restored.causes_unavailability is True
        assert abs(restored.unavailability_fraction - 0.5) < 1e-10


class TestTaskGroup:
    def test_roundtrip_dict(self):
        tg = TaskGroup(
            group_id="TG-001",
            omschrijving="Jaarlijkse ronde",
            taak_type=TaskType.IN,
            interval_jaar=1.0,
            duration=TimeDuration(1.0, TimeUnit.DAYS),
            cost_eur=1500.0,
        )
        restored = TaskGroup.from_dict(tg.to_dict())
        assert restored.group_id == "TG-001"
        assert restored.taak_type == TaskType.IN


class TestRCMProject:
    def _make_project(self) -> RCMProject:
        config = RCMConfig(lifecycle_years=80.0, modeljaar=2026)
        pbs = PBSItem("PBS-001", "Object A", "Element 1", "Bouwdeel X", bouwjaar=2006, ontwerpleeftijd_jaar=40.0)
        func = Functie("FUNC-001", "PBS-001", "Draagfunctie")
        fm = Faalwijze(
            "FM-001", "PBS-001", "FUNC-001", "Corrosie",
            failure_type=FailureType.RANDOM, mttf_jaar=20.0,
            downtime_per_failure=TimeDuration(48.0, TimeUnit.HOURS),
            cost_cm_eur=5000.0,
        )
        pm = PMTask("PM-001", "FM-001", TaskType.SVO, interval_jaar=1.0,
                    duration=TimeDuration(4.0, TimeUnit.HOURS), cost_eur=200.0)
        return RCMProject(
            config=config,
            pbs_items={"PBS-001": pbs},
            functies={"FUNC-001": func},
            faalwijzes={"FM-001": fm},
            pm_tasks={"PM-001": pm},
        )

    def test_get_faalwijzes_for_pbs(self):
        project = self._make_project()
        fms = project.get_faalwijzes_for_pbs("PBS-001")
        assert len(fms) == 1
        assert fms[0].fm_id == "FM-001"

    def test_get_pm_tasks_for_fm(self):
        project = self._make_project()
        tasks = project.get_pm_tasks_for_fm("FM-001")
        assert len(tasks) == 1
        assert tasks[0].pm_id == "PM-001"

    def test_roundtrip_dict(self):
        project = self._make_project()
        restored = RCMProject.from_dict(project.to_dict())
        assert restored.config.lifecycle_years == 80.0
        assert "PBS-001" in restored.pbs_items
        assert "FM-001" in restored.faalwijzes
        assert restored.faalwijzes["FM-001"].failure_type == FailureType.RANDOM
