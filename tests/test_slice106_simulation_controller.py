"""Slice 106 issue 04 — SimulationWorkspaceController."""

from __future__ import annotations

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.simulation_engine_service import MCRunResult
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.simulation_workspace_controller import (
    SimulationWorkspaceController,
    WorkspaceRunContext,
)


def _ctx(**kwargs) -> WorkspaceRunContext:
    base = {
        "run_mode": RunMode.ANALYTICAL,
        "project_path": None,
        "fm_cache_available": False,
        "planning_overlay": PlanningOverlayState.inactive(),
    }
    base.update(kwargs)
    return WorkspaceRunContext(**base)


def test_plan_start_analyse_analytical_with_cache() -> None:
    plan = SimulationWorkspaceController.plan_start_analyse(
        _ctx(project_path="/tmp/p.rcm.json", fm_cache_available=True)
    )
    assert plan is not None
    assert plan.mode == "analytical"
    assert plan.force_recompute is True
    assert plan.compare_slot is None


def test_plan_start_analyse_monte_carlo() -> None:
    plan = SimulationWorkspaceController.plan_start_analyse(
        _ctx(run_mode=RunMode.MONTE_CARLO)
    )
    assert plan is not None
    assert plan.mode == "monte_carlo"
    assert plan.compare_slot is None


def test_plan_compare_slot_run_only_in_mc() -> None:
    assert (
        SimulationWorkspaceController.plan_compare_slot_run(_ctx(), "compare_a") is None
    )
    plan = SimulationWorkspaceController.plan_compare_slot_run(
        _ctx(run_mode=RunMode.MONTE_CARLO),
        "compare_a",
    )
    assert plan is not None
    assert plan.compare_slot == "compare_a"


def test_plan_mc_result_apply_compare_slot() -> None:
    result = MCRunResult(
        status="done",
        n_completed=10,
        seed=1,
    )
    plan = SimulationWorkspaceController.plan_mc_result_apply(
        _ctx(pending_compare_slot="compare_a", run_mode=RunMode.MONTE_CARLO),
        result,
    )
    assert plan.compare_slot == "compare_a"
    assert plan.apply_variant_live is False


def test_plan_mc_result_apply_variant_when_no_slot() -> None:
    result = MCRunResult(
        status="done",
        n_completed=10,
        seed=1,
    )
    plan = SimulationWorkspaceController.plan_mc_result_apply(
        _ctx(variant_mode=True, run_mode=RunMode.MONTE_CARLO),
        result,
    )
    assert plan.compare_slot is None
    assert plan.apply_variant_live is True
