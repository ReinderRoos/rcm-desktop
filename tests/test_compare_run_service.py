from __future__ import annotations

from unittest.mock import patch

import pytest

from rcm_desktop.adapter.compare_run_service import (
    CompareRunConfig,
    CompareRunService,
)
from rcm_desktop.adapter.compare_slot_label import build_compare_slot_label
from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.run_service import RunMetrics, RunResult


class _FakeProject:
    pass


def _metrics() -> RunMetrics:
    return RunMetrics(fm_result_count=0, total_lifecycle_faalmomenten=0.0, total_cost_eur=0.0)


def _done_run() -> RunResult:
    return RunResult(status="done", summary="ok", metrics=_metrics())


def test_run_slot_returns_snapshot_on_success():
    overlay = PlanningOverlayState.inactive()
    config = CompareRunConfig(scenario_key=None, planning_overlay=overlay)
    project = _FakeProject()

    with patch(
        "rcm_desktop.adapter.compare_run_service.execute_planning_run",
    ) as exec_mock:
        from rcm_desktop.adapter.planning_run_service import PlanningRunOutcome

        exec_mock.return_value = PlanningRunOutcome(
            status="done",
            summary="ok",
            run_result=_done_run(),
            project_used=project,
        )
        with patch(
            "rcm_desktop.adapter.compare_run_service.build_contribution_presentation",
            return_value=None,
        ):
            result = CompareRunService.run_slot(project, "/tmp/p.rcm.json", config)

    assert result.status == "done"
    assert result.snapshot is not None
    assert result.snapshot.run_result.status == "done"
    assert result.snapshot.scenario_key is None
    assert result.snapshot.overlay_at_run == overlay
    assert result.snapshot.label == build_compare_slot_label(
        COMPARE_SLOT_A,
        scenario_key=None,
        overlay=overlay,
    )


def test_run_slot_uses_cm_scenario_materialization():
    overlay = PlanningOverlayState.inactive()
    config = CompareRunConfig(scenario_key="cm", planning_overlay=overlay)
    project = _FakeProject()
    cm_clone = _FakeProject()

    with patch(
        "rcm_desktop.adapter.compare_run_service.execute_planning_run",
    ) as exec_mock:
        from rcm_desktop.adapter.planning_run_service import PlanningRunOutcome

        exec_mock.return_value = PlanningRunOutcome(
            status="done",
            summary="ok",
            run_result=_done_run(),
            project_used=cm_clone,
        )
        with patch(
            "rcm_desktop.adapter.compare_run_service.build_contribution_presentation",
            return_value=None,
        ):
            result = CompareRunService.run_slot(project, "/tmp/p.rcm.json", config)

    exec_mock.assert_called_once()
    req = exec_mock.call_args[0][0]
    assert req.materialize_scenario == "cm"
    assert req.scenario_motor_key == "CM"
    assert result.status == "done"
    assert result.snapshot is not None
    assert result.snapshot.scenario_key == "cm"


def test_run_slot_returns_error_without_snapshot():
    config = CompareRunConfig(
        scenario_key=None,
        planning_overlay=PlanningOverlayState.inactive(),
    )
    failed = RunResult(status="error", summary="fail", metrics=_metrics())

    with patch(
        "rcm_desktop.adapter.compare_run_service.execute_planning_run",
    ) as exec_mock:
        from rcm_desktop.adapter.planning_run_service import PlanningRunOutcome

        exec_mock.return_value = PlanningRunOutcome(
            status="error",
            summary="fail",
            run_result=None,
            project_used=None,
        )
        result = CompareRunService.run_slot(_FakeProject(), "/tmp/p.rcm.json", config)

    assert result.status == "error"
    assert result.snapshot is None
    assert "fail" in result.summary
