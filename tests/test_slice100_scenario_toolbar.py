"""Slice 100 issue 06 — scenario workflow toolbar visibility."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_desktop import messages
from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.scenario_workflow_binding import plan_scenario_workflow_chrome
from rcm_desktop.adapter.scenario_workflow_service import LiveRunSnapshot, ScenarioWorkflowService
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app


def test_compare_toggle_label_is_vergelijk_scenarios():
    assert messages.WORKSPACE_COMPARE_TOGGLE_LABEL == "Vergelijk scenario's"


def test_compare_toggle_enabled_only_when_both_filled():
    off = plan_scenario_workflow_chrome(
        validation_ok=True,
        live_run_available_flag=True,
        both_filled=False,
        has_any_scenario=True,
        busy=False,
    )
    on = plan_scenario_workflow_chrome(
        validation_ok=True,
        live_run_available_flag=True,
        both_filled=True,
        has_any_scenario=True,
        busy=False,
    )
    assert off.compare_toggle_enabled is False
    assert on.compare_toggle_enabled is True


def test_clear_compare_visible_when_any_scenario():
    empty = plan_scenario_workflow_chrome(
        validation_ok=True,
        live_run_available_flag=False,
        both_filled=False,
        has_any_scenario=False,
        busy=False,
    )
    filled = plan_scenario_workflow_chrome(
        validation_ok=True,
        live_run_available_flag=True,
        both_filled=False,
        has_any_scenario=True,
        busy=False,
    )
    assert empty.clear_compare_visible is False
    assert filled.clear_compare_visible is True


def test_run_ab_buttons_absent_from_toolbar(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.run_slot_a_button.isVisible() is False
    assert window.run_slot_b_button.isVisible() is False
    assert window.extra_scenario_button.isVisible() is True


def _run() -> RunResult:
    return RunResult(
        status="done",
        summary="ok",
        metrics=RunMetrics(
            fm_result_count=0,
            total_lifecycle_faalmomenten=0.0,
            total_cost_eur=0.0,
        ),
    )


def test_wis_vergelijking_clears_scenarios(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    svc = window._scenario_workflow
    live = LiveRunSnapshot(
        run_mode=RunMode.ANALYTICAL,
        run_result=_run(),
        mc_run=None,
        overlay=PlanningOverlayState.inactive(),
        scenario_key=None,
        presentation=None,
    )
    svc.freeze_live_as_scenario_1(live)
    svc.put_scenario_2(live)
    app.processEvents()

    window.clear_compare_button.click()
    app.processEvents()

    assert not svc.has(COMPARE_SLOT_A)
