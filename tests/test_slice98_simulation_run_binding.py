"""Slice 98 issue 06 — run-modus wiring (adapter seam)."""

from __future__ import annotations

from rcm_core.config import RCMConfig
from rcm_core.models import FailureType, Faalwijze, Functie, PBSItem, RCMProject
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.simulation_engine_service import run_monte_carlo
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.simulation_workspace_service import (
    fm_detail_source_for_run_mode,
    monte_carlo_params_from_project,
    resolve_run_mode,
    session_has_analytical_points,
    session_has_mc_bands,
    start_analyse_uses_monte_carlo,
    top10_lcc_reads_analytical_slot,
)


def _project() -> RCMProject:
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


def test_monte_carlo_run_mode_dispatches_to_mc_runner():
    assert start_analyse_uses_monte_carlo(RunMode.MONTE_CARLO) is True
    assert start_analyse_uses_monte_carlo(RunMode.ANALYTICAL) is False


def test_mode_switch_without_rerun_preserves_dual_namespaces():
    project = _project()
    analytical = RunResult(
        status="done",
        summary="ok",
        metrics=RunMetrics(fm_result_count=0, total_lifecycle_faalmomenten=0.0, total_cost_eur=0.0),
    )
    mc = run_monte_carlo(project, n=200, seed=5)
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=analytical, mc_run=mc)

    assert session_has_analytical_points(session)
    assert session_has_mc_bands(session)
    assert fm_detail_source_for_run_mode(RunMode.ANALYTICAL, session) == "analytical"
    assert fm_detail_source_for_run_mode(RunMode.MONTE_CARLO, session) == "mc_bands"


def test_combo_change_alone_does_not_imply_fake_job():
    assert resolve_run_mode(RunMode.MONTE_CARLO) is RunMode.MONTE_CARLO
    assert resolve_run_mode(None) is RunMode.ANALYTICAL


def test_top10_lcc_ignore_mc_slot():
    project = _project()
    mc = run_monte_carlo(project, n=200, seed=2)
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=None, mc_run=mc)
    assert top10_lcc_reads_analytical_slot(session) is False
    assert session_has_mc_bands(session)


def test_mc_cancel_then_analytical_still_available():
    project = _project()
    analytical = RunResult(
        status="done",
        summary="ok",
        metrics=RunMetrics(fm_result_count=1, total_lifecycle_faalmomenten=1.0, total_cost_eur=1.0),
    )
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=analytical, mc_run=None)
    assert session_has_analytical_points(session)
    assert start_analyse_uses_monte_carlo(RunMode.ANALYTICAL) is False


def test_monte_carlo_params_from_project_config():
    project = _project()
    params = monte_carlo_params_from_project(project)
    assert params.n == 500
    assert params.seed is None
