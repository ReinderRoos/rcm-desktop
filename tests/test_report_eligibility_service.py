from __future__ import annotations

import json
from pathlib import Path

from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    COMPARE_SLOT_B,
    CompareSlotSnapshot,
    CompareSlotState,
)
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.report_eligibility_service import (
    assess_report_eligibility,
    assess_report_workspace,
)
from rcm_desktop.adapter.run_service import RunMetrics, RunResult, run as run_single
from rcm_core.models import RCMProject


def _sample_project() -> RCMProject:
    raw = json.loads(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def test_cannot_generate_without_done_run() -> None:
    result = assess_report_eligibility(last_run=None, compare_slots=None)
    assert result.can_generate is False
    assert result.reason


def test_can_generate_with_done_last_run() -> None:
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    run_result = run_single(project, path)
    result = assess_report_eligibility(last_run=run_result, compare_slots=None)
    assert result.can_generate is True


def _done_run(tag: str = "r") -> RunResult:
    return RunResult(
        status="done",
        summary=tag,
        metrics=RunMetrics(
            fm_result_count=0,
            total_lifecycle_faalmomenten=0.0,
            total_cost_eur=0.0,
        ),
    )


def test_assess_report_workspace_eligible_with_bundle_for_done_run() -> None:
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    run_result = run_single(project, path)
    assessment = assess_report_workspace(
        last_run=run_result,
        compare_slots=None,
        live_overlay=PlanningOverlayState.inactive(),
    )
    assert assessment.eligible is True
    assert assessment.reason == ""
    assert assessment.bundle is not None
    assert assessment.bundle.mode == "single"


def test_assess_report_workspace_ineligible_without_run() -> None:
    assessment = assess_report_workspace(
        last_run=None,
        compare_slots=None,
        live_overlay=None,
    )
    assert assessment.eligible is False
    assert assessment.reason
    assert assessment.bundle is None


def test_assess_report_workspace_compare_both_filled() -> None:
    overlay = PlanningOverlayState.inactive()
    slots = CompareSlotState()
    for key, tag in ((COMPARE_SLOT_A, "a"), (COMPARE_SLOT_B, "b")):
        slots.put(
            key,
            CompareSlotSnapshot.from_motor_run(
                run_result=_done_run(tag),
                presentation=None,
                scenario_key=None if key == COMPARE_SLOT_A else "pm",
                overlay_at_run=overlay,
                label=tag,
            ),
        )
    assessment = assess_report_workspace(
        last_run=None,
        compare_slots=slots,
        live_overlay=None,
    )
    assert assessment.eligible is True
    assert assessment.bundle is not None
    assert assessment.bundle.mode == "compare"
    assert len(assessment.bundle.scenarios) == 2


def test_cannot_generate_with_non_done_last_run() -> None:
    bad = RunResult(
        status="error",
        summary="x",
        metrics=RunMetrics(
            fm_result_count=0,
            total_lifecycle_faalmomenten=0.0,
            total_cost_eur=0.0,
        ),
    )
    result = assess_report_eligibility(last_run=bad, compare_slots=None)
    assert result.can_generate is False
