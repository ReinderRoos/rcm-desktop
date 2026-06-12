"""Tests for lifecycle horizon semantics (AW MC parity)."""

from __future__ import annotations

import pytest

from rcm_core.config import RCMConfig
from rcm_core.distributions import expected_failures_lifecycle
from rcm_core.engine import run_analytical
from rcm_core.lifecycle_horizon import effective_lifecycle_end_age, study_duration_years
from rcm_core.models import FailureType, Faalwijze, Functie, PBSItem, RCMProject


def test_effective_lifecycle_end_age_modes() -> None:
    assert effective_lifecycle_end_age(80.0, 20.0, aw_mc_horizon=False) == 80.0
    assert effective_lifecycle_end_age(80.0, 20.0, aw_mc_horizon=True) == 100.0
    assert study_duration_years(80.0, 20.0, aw_mc_horizon=False) == 60.0
    assert study_duration_years(80.0, 20.0, aw_mc_horizon=True) == 80.0


def test_aw_mc_horizon_increases_expected_failures_for_random() -> None:
    pbs = PBSItem("PBS-1", "Obj", "El", "BD", bouwjaar=2000)
    func = Functie("F-1", "PBS-1", "Functie")
    fm = Faalwijze(
        "FM-R",
        "PBS-1",
        "F-1",
        "Random",
        failure_type=FailureType.RANDOM,
        mttf_jaar=10.0,
    )
    cfg_default = RCMConfig(lifecycle_years=80.0, modeljaar=2026, aw_mc_lifecycle_horizon=False)
    cfg_aw = RCMConfig(lifecycle_years=80.0, modeljaar=2026, aw_mc_lifecycle_horizon=True)
    project_default = RCMProject(
        config=cfg_default,
        pbs_items={"PBS-1": pbs},
        functies={"F-1": func},
        faalwijzes={"FM-R": fm},
    )
    project_aw = RCMProject(
        config=cfg_aw,
        pbs_items={"PBS-1": pbs},
        functies={"F-1": func},
        faalwijzes={"FM-R": fm},
    )
    results_default, _ = run_analytical(project_default, parallel=False)
    results_aw, _ = run_analytical(project_aw, parallel=False)
    assert results_aw["FM-R"].expected_failures > results_default["FM-R"].expected_failures


def test_horizon_forward_matches_aw_mc_config() -> None:
    current_age = 20.0
    end_default = effective_lifecycle_end_age(80.0, current_age, aw_mc_horizon=False)
    end_aw = effective_lifecycle_end_age(80.0, current_age, aw_mc_horizon=True)
    ef_default = expected_failures_lifecycle(
        current_age=current_age,
        lifecycle_years=end_default,
        failure_type="random",
        mttf=10.0,
        sigma=0.0,
        repair_quality=1.0,
    )
    ef_aw = expected_failures_lifecycle(
        current_age=current_age,
        lifecycle_years=end_aw,
        failure_type="random",
        mttf=10.0,
        sigma=0.0,
        repair_quality=1.0,
    )
    assert ef_aw == pytest.approx(ef_default * (80.0 / 60.0))
