"""Slice 100 issue 05 — Extra scenario + variant scenario 2 run."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A, COMPARE_SLOT_B
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.scenario_workflow_binding import plan_scenario_workflow_chrome
from rcm_desktop.adapter.scenario_workflow_service import LiveRunSnapshot, ScenarioWorkflowService
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.validate_service import ValidateResult
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app, _inject_run, _three_level_project


def _run(tag: str = "r") -> RunResult:
    return RunResult(
        status="done",
        summary=tag,
        metrics=RunMetrics(
            fm_result_count=1,
            total_lifecycle_faalmomenten=1.0,
            total_cost_eur=1.0,
        ),
    )


def test_extra_scenario_disabled_before_first_live_run():
    plan = plan_scenario_workflow_chrome(
        validation_ok=True,
        live_run_available_flag=False,
        both_filled=False,
        has_any_scenario=False,
        busy=False,
    )
    assert plan.extra_scenario_enabled is False


def test_extra_scenario_enabled_after_live_run():
    plan = plan_scenario_workflow_chrome(
        validation_ok=True,
        live_run_available_flag=True,
        both_filled=False,
        has_any_scenario=False,
        busy=False,
    )
    assert plan.extra_scenario_enabled is True


def test_enter_extra_scenario_freezes_scenario_1_once():
    svc = ScenarioWorkflowService()
    overlay = PlanningOverlayState.inactive()
    live = LiveRunSnapshot(
        run_mode=RunMode.ANALYTICAL,
        run_result=_run("live"),
        mc_run=None,
        overlay=overlay,
        scenario_key="pm",
        presentation=None,
    )
    svc.enter_extra_scenario(live)
    s1 = svc.get_scenario_1()
    assert s1 is not None
    assert s1.scenario_key == "pm"
    assert svc.variant_mode is True

    live2 = LiveRunSnapshot(
        run_mode=RunMode.ANALYTICAL,
        run_result=_run("live2"),
        mc_run=None,
        overlay=overlay.begin_what_if(),
        scenario_key="cm",
        presentation=None,
    )
    svc.enter_extra_scenario(live2)
    assert svc.get_scenario_1() is s1


def test_variant_start_analyse_fills_scenario_2():
    svc = ScenarioWorkflowService()
    overlay = PlanningOverlayState.inactive()
    svc.enter_extra_scenario(
        LiveRunSnapshot(
            run_mode=RunMode.ANALYTICAL,
            run_result=_run("s1"),
            mc_run=None,
            overlay=overlay,
            scenario_key=None,
            presentation=None,
        )
    )
    svc.apply_variant_live_run(
        LiveRunSnapshot(
            run_mode=RunMode.ANALYTICAL,
            run_result=_run("s2"),
            mc_run=None,
            overlay=overlay.begin_what_if(),
            scenario_key="cm",
            presentation=None,
        )
    )
    assert svc.both_filled()
    assert svc.get_scenario_2() is not None
    assert svc.get_scenario_2().run_result.summary == "s2"


def test_window_extra_scenario_smoke(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    app.processEvents()

    assert window.extra_scenario_button.isEnabled() is False
    _inject_run(window, project)
    app.processEvents()

    assert window.extra_scenario_button.isEnabled() is True
    window.extra_scenario_button.click()
    app.processEvents()

    assert window._scenario_workflow.has(COMPARE_SLOT_A)
    assert not window._scenario_workflow.both_filled()

    _inject_run(window, project)
    app.processEvents()

    assert window._scenario_workflow.both_filled()
