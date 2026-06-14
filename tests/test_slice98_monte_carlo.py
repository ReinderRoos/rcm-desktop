"""Slice 98 — Monte Carlo engine v1 (core)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.config import RCMConfig
from rcm_core.engine import compute_fm_result
from rcm_core.models import (
    AgingDistribution,
    FailureType,
    Faalwijze,
    Functie,
    PBSItem,
    PMTask,
    RCMProject,
    TaskType,
)
from rcm_core.distributions import build_rev_schedule
from rcm_core.simulation_engine import (
    MetricBand,
    SimulationEngine,
    _fm_study_context,
    _simulate_aging_failures_count,
)


def _random_fm_project(*, mttf: float = 10.0, lifecycle_years: float = 80.0) -> RCMProject:
    from rcm_core.units import TimeDuration, TimeUnit

    cfg = RCMConfig(lifecycle_years=lifecycle_years, modeljaar=2026)
    pbs = PBSItem("PBS-1", "Obj", "El", "BD", bouwjaar=2000)
    func = Functie("F-1", "PBS-1", "Functie")
    fm = Faalwijze(
        "FM-R",
        "PBS-1",
        "F-1",
        "Random pump",
        failure_type=FailureType.RANDOM,
        mttf_jaar=mttf,
        cost_cm_eur=1000.0,
        downtime_per_failure=TimeDuration(24.0, TimeUnit.HOURS),
    )
    return RCMProject(
        config=cfg,
        pbs_items={"PBS-1": pbs},
        functies={"F-1": func},
        faalwijzes={"FM-R": fm},
    )


def test_seeded_mc_is_stable():
    project = _random_fm_project()
    engine = SimulationEngine()
    first = engine.run(project, n=500, seed=12345)
    second = engine.run(project, n=500, seed=12345)
    assert first["FM-R"].failures.p50 == second["FM-R"].failures.p50
    assert first["FM-R"].downtime_hr.p50 == second["FM-R"].downtime_hr.p50
    assert first["FM-R"].total_cost_eur.p50 == second["FM-R"].total_cost_eur.p50


def test_fmmc_result_has_metric_bands_and_metadata():
    project = _random_fm_project()
    engine = SimulationEngine()
    results = engine.run(project, n=200, seed=7)
    mc = results["FM-R"]
    assert mc.fm_id == "FM-R"
    assert mc.pbs_id == "PBS-1"
    assert mc.n_completed == 200
    assert mc.seed == 7
    for band in (mc.failures, mc.downtime_hr, mc.total_cost_eur):
        assert isinstance(band, MetricBand)
        assert band.p10 <= band.p50 <= band.p90


def test_random_fm_p50_aligns_with_analytical():
    project = _random_fm_project(mttf=10.0)
    fm = project.faalwijzes["FM-R"]
    pbs = project.pbs_items[fm.pbs_id]
    analytical = compute_fm_result(
        fm,
        pbs,
        [],
        project.task_groups,
        project.config,
        all_pbs=project.pbs_items,
    )
    engine = SimulationEngine()
    mc = engine.run(project, n=8000, seed=99)["FM-R"]
    assert mc.failures.p50 == pytest.approx(analytical.expected_failures, rel=0.08)
    assert mc.downtime_hr.p50 == pytest.approx(
        analytical.expected_total_downtime_hr, rel=0.08
    )
    assert mc.total_cost_eur.p50 == pytest.approx(analytical.total_cost_eur, rel=0.08)


def test_cancel_check_stops_before_n_completed():
    project = _random_fm_project()
    engine = SimulationEngine()
    calls = {"n": 0}

    def cancel_after_three() -> bool:
        calls["n"] += 1
        return calls["n"] > 3

    results = engine.run(project, n=100, seed=1, cancel_check=cancel_after_three)
    mc = results["FM-R"]
    assert mc.n_completed == 3


def _aging_fm_project(
    *,
    aging_distribution: AgingDistribution = AgingDistribution.NORMAL,
    beta_jaar: float = 0.0,
    aw_mc_horizon: bool = False,
    bouwjaar: int = 2026,
    lifecycle_years: float = 60.0,
) -> RCMProject:
    cfg = RCMConfig(
        lifecycle_years=lifecycle_years,
        modeljaar=2026,
        aw_mc_lifecycle_horizon=aw_mc_horizon,
    )
    pbs = PBSItem("PBS-1", "Obj", "El", "BD", bouwjaar=bouwjaar)
    func = Functie("F-1", "PBS-1", "Functie")
    fm = Faalwijze(
        "FM-A",
        "PBS-1",
        "F-1",
        "Aging",
        failure_type=FailureType.AGING,
        mttf_jaar=20.0,
        sigma_jaar=4.0,
        repair_quality=0.7,
        aging_distribution=aging_distribution,
        beta_jaar=beta_jaar,
    )
    return RCMProject(
        config=cfg,
        pbs_items={"PBS-1": pbs},
        functies={"F-1": func},
        faalwijzes={"FM-A": fm},
    )


def _aging_path_mean(
    project: RCMProject,
    *,
    n: int,
    seed: int,
    pm_tasks: list | None = None,
) -> float:
    fm = next(iter(project.faalwijzes.values()))
    pbs = project.pbs_items[fm.pbs_id]
    current_age, study_duration, eff_mult, _ = _fm_study_context(
        fm, pbs, project.config, project.pbs_items
    )
    pm_tasks = pm_tasks if pm_tasks is not None else project.get_pm_tasks_for_fm(fm.fm_id)
    rev_schedule = build_rev_schedule(pm_tasks) if fm.failure_type == FailureType.AGING else ()
    rng = np.random.default_rng(seed)
    sigma = fm.effective_sigma(project.config.default_sigma_fraction)
    samples = [
        _simulate_aging_failures_count(
            current_age=current_age,
            study_duration_years=study_duration,
            mttf=fm.mttf_jaar,
            sigma=sigma,
            repair_quality=fm.repair_quality,
            aging_distribution=fm.aging_distribution.value,
            beta_jaar=fm.beta_jaar,
            rev_schedule=rev_schedule,
            rng=rng,
        )
        * eff_mult
        for _ in range(n)
    ]
    return float(np.mean(samples))


@pytest.mark.parametrize(
    "aging_distribution,beta",
    [
        (AgingDistribution.NORMAL, 0.0),
        (AgingDistribution.TRUNCATED_NORMAL_0, 0.0),
        (AgingDistribution.WEIBULL_2P, 2.5),
    ],
)
def test_aging_mean_aligns_with_analytical(aging_distribution, beta):
    project = _aging_fm_project(aging_distribution=aging_distribution, beta_jaar=beta)
    fm = project.faalwijzes["FM-A"]
    pbs = project.pbs_items[fm.pbs_id]
    analytical = compute_fm_result(
        fm,
        pbs,
        [],
        project.task_groups,
        project.config,
        all_pbs=project.pbs_items,
    )
    mean_failures = _aging_path_mean(project, n=6000, seed=11)
    assert mean_failures == pytest.approx(analytical.expected_failures, rel=0.05)


def test_aging_with_rev_matches_analytical_within_tolerance():
    project = _aging_fm_project()
    fm = project.faalwijzes["FM-A"]
    rev = PMTask(
        pm_id="REV-1",
        fm_id="FM-A",
        taak_type=TaskType.REV,
        interval_jaar=10.0,
        aging_effect_pct=100.0,
    )
    project.pm_tasks["REV-1"] = rev
    pbs = project.pbs_items[fm.pbs_id]
    analytical = compute_fm_result(
        fm,
        pbs,
        [rev],
        project.task_groups,
        project.config,
        all_pbs=project.pbs_items,
    )
    mean_failures = _aging_path_mean(project, n=6000, seed=21, pm_tasks=[rev])
    assert mean_failures == pytest.approx(analytical.expected_failures, rel=0.05)


def test_aw_mc_horizon_changes_study_duration():
    standard = _aging_fm_project(aw_mc_horizon=False, bouwjaar=2000, lifecycle_years=80.0)
    aw = _aging_fm_project(aw_mc_horizon=True, bouwjaar=2000, lifecycle_years=80.0)
    std_mean = _aging_path_mean(standard, n=4000, seed=5)
    aw_mean = _aging_path_mean(aw, n=4000, seed=5)
    assert std_mean != pytest.approx(aw_mean, rel=0.05)


def test_shared_task_group_pm_not_double_counted_per_path():
    from tests.test_parallel_task_group_dedup import _shared_task_group_project

    from rcm_core.engine import run_analytical

    project = _shared_task_group_project()
    analytical, _ = run_analytical(project, parallel=False)
    engine = SimulationEngine()
    mc = engine.run(project, n=1500, seed=42)
    fm1 = mc["FM-1"]
    fm2 = mc["FM-2"]
    undeduplicated_pm_upper = analytical["FM-1"].pm_cost_eur * 2
    assert fm1.total_cost_eur.p50 <= undeduplicated_pm_upper
    assert fm2.total_cost_eur.p50 <= analytical["FM-2"].total_cost_eur * 1.5
    assert fm1.total_cost_eur.p50 == pytest.approx(
        analytical["FM-1"].total_cost_eur, rel=0.25
    )


# --- Slice 98 issue 11: CI regression harness (namespace + cancel seams) ---
# Suggested CI subset:
#   pytest tests/test_slice98_monte_carlo.py tests/test_slice98_simulation_adapter.py \
#     tests/test_slice98_simulation_runner.py tests/test_slice95_monte_carlo.py \
#     tests/test_aging_monte_carlo.py tests/test_background_runner.py -q
# CACHE_INPUTS_VERSION: unchanged — MC-only paths do not alter analytical input hashing.


def test_adapter_cancel_leaves_empty_mc_payload():
    from rcm_desktop.adapter.simulation_engine_service import run_monte_carlo

    project = _random_fm_project()
    calls = {"n": 0}

    def cancel_after_two() -> bool:
        calls["n"] += 1
        return calls["n"] > 2

    result = run_monte_carlo(project, n=100, seed=1, cancel_check=cancel_after_two)
    assert result.status == "cancelled"
    assert result.rows == ()
    assert result.fm_results == {}


def test_dual_namespace_session_preserves_analytical_after_mc():
    from rcm_desktop.adapter.loaded_project import LoadedProject
    from rcm_desktop.adapter.project_session import ProjectSession
    from rcm_desktop.adapter.run_service import RunMetrics, RunResult
    from rcm_desktop.adapter.simulation_engine_service import run_monte_carlo

    project = _random_fm_project()
    analytical = RunResult(
        status="done",
        summary="ok",
        metrics=RunMetrics(fm_result_count=1, total_lifecycle_faalmomenten=1.0, total_cost_eur=1.0),
    )
    mc = run_monte_carlo(project, n=200, seed=9)
    session = ProjectSession.from_parts(
        LoadedProject.from_core(project),
        run=analytical,
        mc_run=mc,
    )
    assert session.run is analytical
    assert session.mc_run is mc
    session_cleared = ProjectSession.from_parts(
        LoadedProject.from_core(project),
        run=analytical,
        mc_run=None,
    )
    assert session_cleared.run is analytical
    assert session_cleared.mc_run is None
