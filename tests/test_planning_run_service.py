from __future__ import annotations

from unittest.mock import patch

import pytest

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_run_service import (
    PlanningRunRequest,
    execute_planning_run,
)
from rcm_desktop.adapter.run_service import RunMetrics, RunResult


class _FakeProject:
    pass


def _metrics() -> RunMetrics:
    return RunMetrics(fm_result_count=0, total_lifecycle_faalmomenten=0.0, total_cost_eur=0.0)


def _done_run() -> RunResult:
    return RunResult(status="done", summary="ok", metrics=_metrics())


def test_execute_planning_run_passes_overlay_and_force_recompute_to_motor():
    overlay = PlanningOverlayState.inactive()
    project = _FakeProject()
    request = PlanningRunRequest(
        project=project,
        project_path="/tmp/p.rcm.json",
        planning_overlay=overlay,
        force_recompute=True,
    )

    with patch(
        "rcm_desktop.adapter.planning_run_service.run_service.run",
        return_value=_done_run(),
    ) as run_mock:
        outcome = execute_planning_run(request)

    run_mock.assert_called_once()
    _, kwargs = run_mock.call_args
    assert kwargs["planning_overlay"] is overlay
    assert kwargs["full_recompute"] is True
    assert outcome.status == "done"
    assert outcome.run_result is not None


def test_execute_planning_run_materializes_cm_scenario_before_motor():
    overlay = PlanningOverlayState.inactive()
    base = _FakeProject()
    cm_clone = _FakeProject()
    request = PlanningRunRequest(
        project=base,
        project_path="/tmp/p.rcm.json",
        planning_overlay=overlay,
        materialize_scenario="cm",
        scenario_motor_key="CM",
    )

    with patch(
        "rcm_desktop.adapter.planning_run_service.build_project_for_scenario",
        return_value=cm_clone,
    ) as build_mock:
        with patch(
            "rcm_desktop.adapter.planning_run_service.run_service.run",
            return_value=_done_run(),
        ) as run_mock:
            outcome = execute_planning_run(request)

    build_mock.assert_called_once_with(base, "CM")
    run_mock.assert_called_once_with(cm_clone, "/tmp/p.rcm.json", full_recompute=False, parallel=False, scenario_key="CM", planning_overlay=overlay)
    assert outcome.status == "done"
    assert outcome.project_used is cm_clone


def test_execute_planning_run_returns_error_when_motor_fails():
    failed = RunResult(status="error", summary="fail", metrics=_metrics())
    request = PlanningRunRequest(
        project=_FakeProject(),
        project_path="/tmp/p.rcm.json",
        planning_overlay=PlanningOverlayState.inactive(),
    )

    with patch(
        "rcm_desktop.adapter.planning_run_service.run_service.run",
        return_value=failed,
    ):
        outcome = execute_planning_run(request)

    assert outcome.status == "error"
    assert outcome.run_result is None
    assert "fail" in outcome.summary
