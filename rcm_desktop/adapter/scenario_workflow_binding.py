"""Adapter helpers for scenario-workflow toolbar + live snapshot capture (slice 100)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.presentation_cache_service import PresentationProjectTotal
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.scenario_workflow_service import LiveRunSnapshot, ScenarioWorkflowService
from rcm_desktop.adapter.simulation_engine_service import MCRunResult
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.simulation_workspace_service import live_run_available, resolve_live_run_result


@dataclass(frozen=True)
class ScenarioWorkflowChromePlan:
    extra_scenario_enabled: bool
    extra_scenario_visible: bool
    compare_toggle_enabled: bool
    compare_toggle_visible: bool
    clear_compare_visible: bool


def plan_scenario_workflow_chrome(
    *,
    validation_ok: bool,
    live_run_available_flag: bool,
    both_filled: bool,
    has_any_scenario: bool,
    busy: bool,
) -> ScenarioWorkflowChromePlan:
    """Visibility rule D (slice 100 issue 06)."""
    can_act = validation_ok and not busy
    return ScenarioWorkflowChromePlan(
        extra_scenario_enabled=can_act and live_run_available_flag,
        extra_scenario_visible=True,
        compare_toggle_enabled=can_act and both_filled,
        compare_toggle_visible=True,
        clear_compare_visible=has_any_scenario,
    )


def capture_live_run_snapshot(
    session: ProjectSession,
    *,
    run_mode: RunMode,
    overlay: PlanningOverlayState,
    scenario_key: str | None,
    presentation: PresentationProjectTotal | None,
    mc_run: MCRunResult | None = None,
) -> LiveRunSnapshot | None:
    """Build a freeze-ready snapshot from the current live run, or None if unavailable."""
    run_result = resolve_live_run_result(session, run_mode)
    if run_result is None or run_result.status != "done":
        return None
    if run_mode is RunMode.MONTE_CARLO:
        effective_mc = mc_run if mc_run is not None else session.mc_run
        if effective_mc is None or effective_mc.status != "done":
            return None
        return LiveRunSnapshot(
            run_mode=run_mode,
            run_result=run_result,
            mc_run=effective_mc,
            overlay=overlay,
            scenario_key=scenario_key,
            presentation=presentation,
        )
    return LiveRunSnapshot(
        run_mode=run_mode,
        run_result=run_result,
        mc_run=None,
        overlay=overlay,
        scenario_key=scenario_key,
        presentation=presentation,
    )


def live_run_ready(session: ProjectSession | None, run_mode: RunMode) -> bool:
    return session is not None and live_run_available(session, run_mode)


def apply_scenario_workflow_chrome(window: object, plan: ScenarioWorkflowChromePlan) -> None:
    extra = getattr(window, "extra_scenario_button", None)
    if extra is not None:
        extra.setVisible(plan.extra_scenario_visible)
        extra.setEnabled(plan.extra_scenario_enabled)
    compare = getattr(window, "compare_toggle_button", None)
    if compare is not None:
        compare.setVisible(plan.compare_toggle_visible)
        compare.setEnabled(plan.compare_toggle_enabled)
    clear_btn = getattr(window, "clear_compare_button", None)
    if clear_btn is not None:
        clear_btn.setVisible(plan.clear_compare_visible)
