from __future__ import annotations

from rcm_desktop.adapter.compare_run_service import CompareRunOutcome
from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    CompareSlotSnapshot,
    CompareSlotState,
)
from rcm_desktop.adapter.compare_workspace_controller import CompareWorkspaceController
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.workspace_render_index import SLOT_A


def _done_run() -> RunResult:
    return RunResult(
        status="done",
        summary="ok",
        metrics=RunMetrics(
            fm_result_count=0,
            total_lifecycle_faalmomenten=0.0,
            total_cost_eur=0.0,
        ),
    )


def test_plan_after_slot_run_returns_render_plan():
    overlay = PlanningOverlayState.inactive()
    snap = CompareSlotSnapshot.from_motor_run(
        run_result=_done_run(),
        presentation=None,
        scenario_key=None,
        overlay_at_run=overlay,
        label="A",
    )
    outcome = CompareRunOutcome(status="done", summary="ok", snapshot=snap)

    plan = CompareWorkspaceController.plan_after_slot_run(
        COMPARE_SLOT_A, outcome, previous_snapshot=None
    )

    assert plan is not None
    assert plan.slot_key == COMPARE_SLOT_A
    assert plan.render_slot_key == SLOT_A
