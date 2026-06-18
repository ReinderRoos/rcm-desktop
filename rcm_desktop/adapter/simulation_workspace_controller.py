"""Simulation start/result planning voor werkruimte (slice 106 issue 04)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.simulation_engine_service import MCRunResult
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.simulation_workspace_service import start_analyse_uses_monte_carlo


@dataclass(frozen=True)
class WorkspaceRunContext:
    run_mode: RunMode
    project_path: str | None
    fm_cache_available: bool
    planning_overlay: PlanningOverlayState
    pending_compare_slot: str | None = None
    variant_mode: bool = False
    compare_mode: bool = False


@dataclass(frozen=True)
class StartAnalysePlan:
    mode: Literal["analytical", "monte_carlo"]
    compare_slot: str | None = None
    force_recompute: bool = False
    planning_overlay: PlanningOverlayState | None = None


@dataclass(frozen=True)
class McResultApplyPlan:
    compare_slot: str | None
    apply_variant_live: bool
    attach_to_store: bool = True
    set_last_mc_run: bool = True
    refresh_status: bool = True
    rerender_detail: bool = True
    update_scenario_chrome: bool = True


class SimulationWorkspaceController:
    """Adapter-controller: views voeren plannen uit, geen dispatch-logica."""

    @staticmethod
    def plan_start_analyse(ctx: WorkspaceRunContext) -> StartAnalysePlan | None:
        if start_analyse_uses_monte_carlo(ctx.run_mode):
            return StartAnalysePlan(
                mode="monte_carlo",
                compare_slot=None,
                planning_overlay=ctx.planning_overlay,
            )
        return StartAnalysePlan(
            mode="analytical",
            force_recompute=bool(ctx.project_path and ctx.fm_cache_available),
            planning_overlay=ctx.planning_overlay,
        )

    @staticmethod
    def plan_compare_slot_run(
        ctx: WorkspaceRunContext,
        slot_key: str,
    ) -> StartAnalysePlan | None:
        if not start_analyse_uses_monte_carlo(ctx.run_mode):
            return None
        return StartAnalysePlan(
            mode="monte_carlo",
            compare_slot=slot_key,
            planning_overlay=ctx.planning_overlay,
        )

    @staticmethod
    def plan_mc_result_apply(
        ctx: WorkspaceRunContext,
        result: MCRunResult,
    ) -> McResultApplyPlan:
        slot_key = ctx.pending_compare_slot
        apply_variant = (
            slot_key is None
            and ctx.variant_mode
            and result.status == "done"
        )
        compare_slot = slot_key if result.status == "done" else None
        return McResultApplyPlan(
            compare_slot=compare_slot,
            apply_variant_live=apply_variant,
        )
