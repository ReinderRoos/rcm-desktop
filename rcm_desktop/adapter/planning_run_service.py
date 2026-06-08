"""Planning-overlay motorrun — één seam voor werkruimte- en A/B-runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rcm_core.models import RCMProject

from rcm_desktop.adapter import run_service
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.run_decision import RunUserIntent, resolve_run_execution
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.scenario_run_service import build_project_for_scenario

_SCENARIO_MATERIALIZE = {"cm": "CM", "pm": "PM"}


@dataclass(frozen=True)
class PlanningRunRequest:
    project: RCMProject
    project_path: str | Path
    planning_overlay: PlanningOverlayState
    force_recompute: bool = False
    materialize_scenario: str | None = None  # "cm" | "pm"
    scenario_motor_key: str | None = None  # "CM" | "PM"


@dataclass(frozen=True)
class PlanningRunOutcome:
    status: str
    summary: str
    run_result: RunResult | None
    project_used: RCMProject | None


def execute_planning_run(request: PlanningRunRequest) -> PlanningRunOutcome:
    """Voer één motorrun uit met overlay- en cache-beleid."""
    run_project = request.project
    if request.materialize_scenario in _SCENARIO_MATERIALIZE:
        run_project = build_project_for_scenario(
            request.project,
            _SCENARIO_MATERIALIZE[request.materialize_scenario],
        )

    intent = (
        RunUserIntent.FORCE_RECOMPUTE
        if request.force_recompute
        else RunUserIntent.START_ANALYSE
    )
    opts = resolve_run_execution(user_intent=intent)
    rr = run_service.run(
        run_project,
        request.project_path,
        full_recompute=opts.full_recompute,
        parallel=opts.parallel,
        planning_overlay=request.planning_overlay,
        scenario_key=request.scenario_motor_key,
    )
    if rr.status != "done":
        return PlanningRunOutcome(
            status="error",
            summary=rr.summary,
            run_result=None,
            project_used=None,
        )
    return PlanningRunOutcome(
        status="done",
        summary=rr.summary,
        run_result=rr,
        project_used=run_project,
    )
