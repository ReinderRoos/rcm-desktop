"""Tests voor validators.py — FK-controles en domeinvalidaties."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.config import RCMConfig
from rcm_core.models import (
    FailureType, Faalwijze, Functie, PBSItem, PMTask, RCMProject, TaskGroup, TaskType
)
from rcm_core.validators import validate_project, ValidationError
from rcm_core.units import TimeDuration, TimeUnit
from rcm_core.persistence import load_project


def _make_valid_project() -> RCMProject:
    config = RCMConfig(lifecycle_years=80.0, modeljaar=2026)
    pbs = PBSItem("PBS-001", "Obj", "El", "BD", bouwjaar=2006, ontwerpleeftijd_jaar=40.0)
    func = Functie("FUNC-001", "PBS-001", "Draagfunctie")
    fm = Faalwijze(
        "FM-001", "PBS-001", "FUNC-001", "Test",
        failure_type=FailureType.RANDOM, mttf_jaar=20.0,
        downtime_per_failure=TimeDuration(1.0, TimeUnit.DAYS),
    )
    pm = PMTask(
        "PM-001", "FM-001", TaskType.IN,
        interval_jaar=1.0,
        duration=TimeDuration(4.0, TimeUnit.HOURS),
        cost_eur=200.0,
    )
    return RCMProject(
        config=config,
        pbs_items={"PBS-001": pbs},
        functies={"FUNC-001": func},
        faalwijzes={"FM-001": fm},
        pm_tasks={"PM-001": pm},
    )


class TestValidators:
    def test_valid_project_has_no_errors(self):
        project = _make_valid_project()
        errors = validate_project(project)
        assert errors == []

    def test_fm_pbs_fk_missing(self):
        project = _make_valid_project()
        project.faalwijzes["FM-001"].pbs_id = "PBS-NIET_BESTAAND"
        errors = validate_project(project)
        codes = [e.code for e in errors]
        assert "FM_PBS_FK" in codes

    def test_fm_mttf_nonpositive(self):
        project = _make_valid_project()
        project.faalwijzes["FM-001"].mttf_jaar = 0.0
        errors = validate_project(project)
        codes = [e.code for e in errors]
        assert "FM_MTTF_NONPOSITIVE" in codes

    def test_pm_fm_fk_missing(self):
        project = _make_valid_project()
        project.pm_tasks["PM-001"].fm_id = "FM-NIET_BESTAAND"
        errors = validate_project(project)
        codes = [e.code for e in errors]
        assert "PM_FM_FK" in codes

    def test_pm_task_group_fk_missing(self):
        project = _make_valid_project()
        project.pm_tasks["PM-001"].task_group_id = "TG-NIET_BESTAAND"
        errors = validate_project(project)
        codes = [e.code for e in errors]
        assert "PM_TG_FK" in codes

    def test_func_pbs_fk_missing(self):
        project = _make_valid_project()
        project.functies["FUNC-001"].pbs_id = "PBS-NIET_BESTAAND"
        errors = validate_project(project)
        codes = [e.code for e in errors]
        assert "FUNC_PBS_FK" in codes

    def test_config_lifecycle_zero(self):
        project = _make_valid_project()
        project.config.lifecycle_years = 0.0
        errors = validate_project(project)
        codes = [e.code for e in errors]
        assert "CFG_LIFECYCLE" in codes

    def test_pbs_multiplicity_zero(self):
        project = _make_valid_project()
        project.pbs_items["PBS-001"].multiplicity = 0
        errors = validate_project(project)
        codes = [e.code for e in errors]
        assert "PBS_MULTIPLICITY" in codes

    def test_sample_fixture_is_valid(self):
        fixture = Path(__file__).parent / "fixtures" / "sample_project.rcm.json"
        project = load_project(fixture)
        errors = validate_project(project)
        assert errors == [], f"Fixture heeft validatiefouten: {errors}"

    def test_pbs_effective_bouwjaar_zero(self):
        project = _make_valid_project()
        project.pbs_items["PBS-001"].bouwjaar = 0  # geen parent → effectief bouwjaar blijft 0
        errors = validate_project(project)
        assert any(e.code == "PBS_EFFECTIVE_BOUWJAAR_ZERO" for e in errors)

    def test_pbs_bouwjaar_older_than_parent(self):
        project = _make_valid_project()
        project.pbs_items["PBS-001"].bouwjaar = 2000
        project.pbs_items["PBS-CHILD"] = PBSItem(
            "PBS-CHILD", "O", "E", "BD", bouwjaar=1990, parent_pbs_id="PBS-001"
        )
        errors = validate_project(project)
        assert any(e.code == "PBS_BOUWJAAR_CHRONOLOGIE" for e in errors)

    def test_fm_random_with_sigma(self):
        project = _make_valid_project()
        project.faalwijzes["FM-001"].failure_type = FailureType.RANDOM
        project.faalwijzes["FM-001"].sigma_jaar = 3.0
        errors = validate_project(project)
        assert any(e.code == "FM_RANDOM_SIGMA_NONZERO" for e in errors)

    def test_sample_fixture_passes_new_validators(self):
        fixture = Path(__file__).parent / "fixtures" / "sample_project.rcm.json"
        project = load_project(fixture)
        errors = validate_project(project)
        new_codes = {"PBS_EFFECTIVE_BOUWJAAR_ZERO", "PBS_BOUWJAAR_CHRONOLOGIE", "FM_RANDOM_SIGMA_NONZERO"}
        assert not any(e.code in new_codes for e in errors), \
            [e for e in errors if e.code in new_codes]
