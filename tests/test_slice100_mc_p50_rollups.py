"""Slice 100 issue 02 — MC P50 rollup + live Top 10/LCC routing (TDD)."""

from __future__ import annotations

import math

import pytest

from rcm_core.config import RCMConfig
from rcm_core.engine import compute_all_fm_results
from rcm_core.effect_impact_service import EffectPresentation, nb_yearly_series
from rcm_core.models import FailureType, Faalwijze, Functie, PBSItem, RCMProject, TaskType

from rcm_desktop.adapter.compare_slot_state import CompareSlotState
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.results_workspace_orchestrator import (
    ResultsWorkspaceOrchestrator,
    WorkspaceRenderContext,
)
from rcm_desktop.adapter.results_workspace_state import MODE_BIJDRAGEN, ResultsWorkspaceState
from rcm_desktop.adapter.simulation_engine_service import (
    build_run_result_from_mc_p50,
    fm_results_from_mc_p50,
    run_monte_carlo,
)
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.simulation_workspace_service import live_run_available, resolve_live_run_result
from rcm_desktop.adapter.workspace_render_index import WorkspaceRenderIndex
from rcm_desktop.adapter.workspace_view_service import build_bijdragen_view
from tests.helpers.lcc_cm_shape import characterize_cm_year_shape, peak_bucket_index


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


def test_build_run_result_from_mc_p50_produces_nonempty_fm_rows():
    project = _project()
    mc = run_monte_carlo(project, n=200, seed=2)
    assert mc.status == "done"

    run = build_run_result_from_mc_p50(project, mc)

    assert run.status == "done"
    assert len(run.fm_core_results) == 1
    assert run.metrics.total_cost_eur > 0
    assert run.metrics.total_lifecycle_faalmomenten > 0


def test_live_run_available_for_mc_only_session():
    project = _project()
    mc = run_monte_carlo(project, n=200, seed=2)
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=None, mc_run=mc)

    assert live_run_available(session, RunMode.MONTE_CARLO)
    assert not live_run_available(session, RunMode.ANALYTICAL)
    assert resolve_live_run_result(session, RunMode.MONTE_CARLO) is not None


def test_build_bijdragen_view_after_mc_only_run():
    project = _project()
    mc = run_monte_carlo(project, n=200, seed=3)
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=None, mc_run=mc)
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_BIJDRAGEN)
    snapshot = ws.snapshot()
    render_index = WorkspaceRenderIndex()

    view = build_bijdragen_view(
        session,
        snapshot,
        render_index=render_index,
        project_total_presentation=None,
        run_mode=RunMode.MONTE_CARLO,
    )

    assert view is not None
    assert len(view.contribution_rows) > 0


def test_plan_render_top10_after_mc_only_run():
    project = _project()
    mc = run_monte_carlo(project, n=200, seed=4)
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=None, mc_run=mc)
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_BIJDRAGEN)
    ctx = WorkspaceRenderContext(
        session=session,
        compare_slots=CompareSlotState(),
        project_total_presentation=None,
        render_index=WorkspaceRenderIndex(),
        prev_lcc_snapshot=None,
        run_mode=RunMode.MONTE_CARLO,
    )
    plan = ResultsWorkspaceOrchestrator.plan_render(ws.snapshot(), ctx)
    assert plan.kind == "bijdragen"
    assert plan.bijdragen is not None
    assert len(plan.bijdragen.contribution_rows) > 0


def _single_fm_project(*, failure_type: str, mttf_jaar: float, lifecycle_years: float) -> RCMProject:
    sigma = round(0.15 * mttf_jaar, 1) if failure_type == "aging" else 0.0
    fm_fields: dict = {
        "fm_id": "FM-1",
        "pbs_id": "PBS-1",
        "functie_id": "F1",
        "faalwijze_omschrijving": "Synth",
        "failure_type": failure_type,
        "mttf_jaar": mttf_jaar,
        "sigma_jaar": sigma,
        "cost_cm_eur": 10_000.0,
        "downtime_per_failure": {"value": 1.0, "unit": "uur"},
    }
    return RCMProject.from_dict(
        {
            "config": {"lifecycle_years": lifecycle_years, "modeljaar": 2026},
            "pbs_items": {
                "PBS-1": {
                    "pbs_id": "PBS-1",
                    "object_naam": "O",
                    "element_naam": "E",
                    "bouwdeel_naam": "B",
                    "component_naam": "",
                    "multiplicity": 1,
                    "bouwjaar": 2026,
                },
            },
            "functies": {},
            "faalwijzes": {"FM-1": fm_fields},
            "pm_tasks": {},
            "task_groups": {},
            "effect_klassen": {},
            "fm_effect_links": {},
            "pm_effect_links": {},
            "bibliotheek": {},
        }
    )


def test_mc_p50_aging_fm_populates_horizon_profile_with_peaked_lcc_buckets():
    mttf = 20.0
    project = _single_fm_project(failure_type="aging", mttf_jaar=mttf, lifecycle_years=30.0)
    mc = run_monte_carlo(project, n=200, seed=2)
    assert mc.status == "done"

    fm_results = fm_results_from_mc_p50(project, mc)
    fmr = fm_results[0]
    assert fmr.horizon_profile is not None
    assert sum(fmr.horizon_profile.cor_eur) > 0.0

    run = build_run_result_from_mc_p50(project, mc)
    shape = characterize_cm_year_shape(project, run.fm_core_results)
    assert shape.reconciles
    assert shape.used_legacy is False
    assert shape.max_mean_ratio > 2.0
    peak_h = peak_bucket_index(shape.buckets)
    target_h = int(mttf) - 1
    assert abs(peak_h - target_h) <= 1


def test_mc_p50_random_fm_horizon_profile_yields_flat_lcc_buckets():
    project = _single_fm_project(failure_type="random", mttf_jaar=10.0, lifecycle_years=20.0)
    mc = run_monte_carlo(project, n=200, seed=3)
    assert mc.status == "done"

    run = build_run_result_from_mc_p50(project, mc)
    fmr = run.fm_core_results[0]
    assert fmr.horizon_profile is not None

    shape = characterize_cm_year_shape(project, run.fm_core_results)
    assert shape.reconciles
    assert shape.used_legacy is False
    assert shape.cv < 0.01


def _nmf_in_only_project() -> RCMProject:
    """NMF with IN-only PM: analytical horizon downtime buckets stay empty."""
    cfg = RCMConfig(lifecycle_years=20.0, modeljaar=2026, monte_carlo_n=200)
    pbs = PBSItem("PBS-1", "Obj", "El", "BD", bouwjaar=2026)
    func = Functie("F-1", "PBS-1", "Functie")
    fm = Faalwijze(
        "FM-NMF",
        "PBS-1",
        "F-1",
        "NMF hidden",
        failure_type=FailureType.RANDOM,
        mttf_jaar=5.0,
        cost_cm_eur=1000.0,
        is_evident=False,
    )
    fm_dict = fm.to_dict()
    fm_dict["downtime_per_failure"] = {"value": 1.0, "unit": "dag"}
    return RCMProject.from_dict(
        {
            "config": cfg.to_dict(),
            "pbs_items": {"PBS-1": pbs.to_dict()},
            "functies": {"F-1": func.to_dict()},
            "faalwijzes": {"FM-NMF": fm_dict},
            "pm_tasks": {
                "PM-IN": {
                    "pm_id": "PM-IN",
                    "fm_id": "FM-NMF",
                    "taak_type": TaskType.IN.value,
                    "interval_jaar": 1.0,
                    "duration": {"value": 1.0, "unit": "uur"},
                    "pm_cost_eur": 0.0,
                },
            },
            "task_groups": {},
            "effect_klassen": {},
            "fm_effect_links": {},
            "pm_effect_links": {},
            "bibliotheek": {},
        }
    )


def test_mc_p50_nb_yearly_series_aligns_with_analytical_for_nmf_in_only():
    project = _nmf_in_only_project()
    anal_results = list(compute_all_fm_results(project).values())
    assert len(anal_results) == 1
    anal_fmr = anal_results[0]
    assert anal_fmr.horizon_profile is not None
    assert sum(anal_fmr.horizon_profile.cor_downtime_hr) == 0.0
    assert anal_fmr.expected_total_downtime_hr > anal_fmr.expected_raw_downtime_hr

    mc = run_monte_carlo(project, n=200, seed=7)
    assert mc.status == "done"
    mc_run = build_run_result_from_mc_p50(project, mc)
    mc_fmr = mc_run.fm_core_results[0]
    assert mc_fmr.horizon_profile is not None
    assert sum(mc_fmr.horizon_profile.cor_downtime_hr) == 0.0
    assert sum(mc_fmr.horizon_profile.hidden_nb_hr) == 0.0

    pres = EffectPresentation(horizon="per_year", unavailability_display="hours")
    anal_nb = nb_yearly_series(project, anal_results, presentation=pres)
    mc_nb = nb_yearly_series(project, mc_run.fm_core_results, presentation=pres)
    assert anal_nb and mc_nb
    assert anal_nb == mc_nb
