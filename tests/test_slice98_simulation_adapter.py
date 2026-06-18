"""Slice 98 issue 04 — adapter MC service tests."""

from __future__ import annotations

from rcm_core.config import RCMConfig
from rcm_core.models import FailureType, Faalwijze, Functie, PBSItem, RCMProject
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.simulation_engine_service import (
    build_mc_fm_rows,
    run_monte_carlo,
)
from rcm_desktop.adapter.simulation_job_service import SimulationResultStore


def _tiny_project() -> RCMProject:
    cfg = RCMConfig(lifecycle_years=80.0, modeljaar=2026, monte_carlo_n=500)
    pbs = PBSItem("PBS-1", "Obj", "El", "BD", bouwjaar=2000)
    func = Functie("F-1", "PBS-1", "Functie")
    fm = Faalwijze(
        "FM-R",
        "PBS-1",
        "F-1",
        "Random",
        failure_type=FailureType.RANDOM,
        mttf_jaar=10.0,
        cost_cm_eur=500.0,
    )
    return RCMProject(
        config=cfg,
        pbs_items={"PBS-1": pbs},
        functies={"F-1": func},
        faalwijzes={"FM-R": fm},
    )


def test_run_monte_carlo_builds_rows_with_ordered_bands():
    project = _tiny_project()
    result = run_monte_carlo(project, n=200, seed=99)
    assert result.status == "done"
    assert result.seed == 99
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.failures_band.p10 <= row.failures_band.p50 <= row.failures_band.p90


def test_fixed_seed_is_reproducible():
    project = _tiny_project()
    first = run_monte_carlo(project, n=200, seed=7)
    second = run_monte_carlo(project, n=200, seed=7)
    assert first.rows[0].failures_band.p50 == second.rows[0].failures_band.p50


def test_mc_run_does_not_overwrite_analytical_session_slot():
    project = _tiny_project()
    analytical = RunResult(
        status="done",
        summary="analytical",
        metrics=RunMetrics(fm_result_count=1, total_lifecycle_faalmomenten=1.0, total_cost_eur=1.0),
    )
    mc = run_monte_carlo(project, n=200, seed=3)
    session = ProjectSession.from_parts(
        LoadedProject.from_core(project),
        run=analytical,
        mc_run=mc,
    )
    assert session.run is analytical
    assert session.mc_run is mc
    assert session.run.fm_core_results == ()


def test_build_mc_fm_rows_count_matches_fm_count():
    project = _tiny_project()
    mc = run_monte_carlo(project, n=200, seed=1)
    rows = build_mc_fm_rows(project, mc.fm_results)
    assert len(rows) == len(project.faalwijzes)


def test_store_preserves_analytical_when_mc_updated():
    store = SimulationResultStore()
    store.set_analytical_run_id("run-a")
    store.set_mc_job_id("mc-1")
    store.set_mc_job_id("mc-2")
    assert store.analytical_run_id == "run-a"


def test_run_monte_carlo_maps_validation_to_user_facing_error():
    project = _tiny_project()
    result = run_monte_carlo(project, n=50, seed=1)
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "CFG_MC_N"
