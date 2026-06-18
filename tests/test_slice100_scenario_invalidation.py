"""Slice 100 issue 04 — scenario slot invalidation hooks."""

from __future__ import annotations

import pytest

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.scenario_workflow_invalidation import (
    ScenarioInvalidationReason,
    clear_scenarios_on_invalidation,
)
from rcm_desktop.adapter.scenario_workflow_service import LiveRunSnapshot, ScenarioWorkflowService
from rcm_desktop.adapter.simulation_job_service import RunMode


def _run(tag: str = "r") -> RunResult:
    return RunResult(
        status="done",
        summary=tag,
        metrics=RunMetrics(
            fm_result_count=0,
            total_lifecycle_faalmomenten=0.0,
            total_cost_eur=0.0,
        ),
    )


@pytest.mark.parametrize(
    "reason",
    list(ScenarioInvalidationReason),
)
def test_invalidation_clears_filled_scenario_slots(reason: ScenarioInvalidationReason):
    svc = ScenarioWorkflowService()
    live = LiveRunSnapshot(
        run_mode=RunMode.ANALYTICAL,
        run_result=_run("live"),
        mc_run=None,
        overlay=PlanningOverlayState.inactive(),
        scenario_key=None,
        presentation=None,
    )
    svc.freeze_live_as_scenario_1(live)
    svc.put_scenario_2(live)
    assert svc.both_filled()

    clear_scenarios_on_invalidation(svc, reason)

    assert not svc.has("A")
    assert not svc.has("B")
    assert not svc.both_filled()
