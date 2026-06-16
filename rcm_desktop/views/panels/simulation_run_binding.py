"""Start-analyse dispatch for analytical vs Monte Carlo (slice 98 issue 06)."""

from __future__ import annotations

from typing import Any

from rcm_desktop.adapter import workspace_session_service as wss
from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A
from rcm_desktop.adapter.scenario_workflow_service import LiveRunSnapshot, ScenarioWorkflowService
from rcm_desktop.adapter.simulation_engine_service import MCRunResult, attach_mc_run_to_store, detach_mc_run
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.simulation_runner import SimulationRunner
from rcm_desktop.adapter.simulation_workspace_service import (
    build_run_result_from_mc_p50,
    monte_carlo_params_from_project,
    start_analyse_uses_monte_carlo,
)
from rcm_desktop.views.panels.simulation_workspace_binding import (
    current_run_mode,
    ensure_simulation_store,
    refresh_simulation_status,
)


def ensure_simulation_runner(window: Any) -> SimulationRunner:
    runner = getattr(window, "_simulation_runner", None)
    if not isinstance(runner, SimulationRunner):
        runner = SimulationRunner()
        window._simulation_runner = runner
        runner.job_changed.connect(lambda job: _on_simulation_job_changed(window, job))
        runner.state_changed.connect(lambda state: _on_simulation_state_changed(window, state))
        runner.result_ready.connect(lambda result: _on_mc_result_ready(window, result))
    return runner


def wire_simulation_run_handlers(window: Any) -> None:
    ensure_simulation_runner(window)
    if hasattr(window, "simulation_run_mode_combo"):
        window.simulation_run_mode_combo.currentIndexChanged.connect(
            lambda _idx: _on_run_mode_changed(window)
        )


def dispatch_start_analyse(window: Any) -> bool:
    session = window._project_session()
    if session is None:
        return False
    run_mode = current_run_mode(window)
    if start_analyse_uses_monte_carlo(run_mode):
        return _start_monte_carlo(window, session, compare_slot_key=None)
    return _start_analytical(window, session)


def dispatch_compare_slot_run(window: Any, slot_key: str) -> bool:
    """Start Run A/B as Monte Carlo when run-modus is MC."""
    if not start_analyse_uses_monte_carlo(current_run_mode(window)):
        return False
    session = window._project_session()
    if session is None:
        return False
    return _start_monte_carlo(window, session, compare_slot_key=slot_key)


def _start_analytical(window: Any, session: Any) -> bool:
    path = window.path_input.text().strip()
    overlay = window.workspace_state.snapshot().planning_overlay
    force = bool(path and wss.fm_cache_available_for_session(session, path))
    if window._run_runner.start(
        wss.editing_project(session),
        path,
        planning_overlay=overlay,
        force_recompute=force,
    ):
        _set_run_controls_busy(window)
        return True
    return False


def _start_monte_carlo(
    window: Any,
    session: Any,
    *,
    compare_slot_key: str | None,
) -> bool:
    if compare_slot_key is not None:
        window._pending_mc_compare_slot = compare_slot_key
    runner = ensure_simulation_runner(window)
    project = wss.editing_project(session)
    params = monte_carlo_params_from_project(project)
    if runner.start(project, n=params.n, seed=params.seed):
        _set_run_controls_busy(window)
        return True
    if compare_slot_key is not None:
        window._pending_mc_compare_slot = None
    return False


def _set_run_controls_busy(window: Any) -> None:
    analyse_btn = getattr(window, "run_analyse_button", None)
    if analyse_btn is not None and analyse_btn.isVisible():
        analyse_btn.setEnabled(False)
    for attr in ("run_slot_a_button", "run_slot_b_button"):
        btn = getattr(window, attr, None)
        if btn is not None:
            btn.setEnabled(False)


def _clear_pending_mc_compare_slot(window: Any) -> None:
    window._pending_mc_compare_slot = None


def _on_simulation_job_changed(window: Any, job: object) -> None:
    window._simulation_job = job
    refresh_simulation_status(window)


def _on_mc_result_ready(window: Any, result: object) -> None:
    if not isinstance(result, MCRunResult):
        return
    store = ensure_simulation_store(window)
    attach_mc_run_to_store(store, result, job_id=f"mc-{result.seed}-{result.n_completed}")
    window._state.set_last_mc_run(result)
    slot_key = getattr(window, "_pending_mc_compare_slot", None)
    workflow = getattr(window, "_scenario_workflow", None)
    if slot_key is not None and result.status == "done" and isinstance(workflow, ScenarioWorkflowService):
        _put_mc_into_compare_slot(window, workflow, slot_key, result)
        _clear_pending_mc_compare_slot(window)
    elif workflow is not None and isinstance(workflow, ScenarioWorkflowService) and workflow.variant_mode and result.status == "done":
        _apply_mc_variant_run(window, workflow, result)
    refresh_simulation_status(window)
    window._rerender_detail_for_current_scope()
    if hasattr(window, "_update_scenario_workflow_chrome"):
        window._update_scenario_workflow_chrome()


def _apply_mc_variant_run(window: Any, workflow: ScenarioWorkflowService, result: MCRunResult) -> None:
    from rcm_desktop.adapter.scenario_workflow_binding import capture_live_run_snapshot
    from rcm_desktop.views.panels.simulation_workspace_binding import current_run_mode

    session = window._project_session()
    if session is None:
        return
    snapshot = window.workspace_state.snapshot()
    live = capture_live_run_snapshot(
        session,
        run_mode=RunMode.MONTE_CARLO,
        overlay=snapshot.planning_overlay,
        scenario_key=window.compare_scenario_combo.currentData(),
        presentation=getattr(window, "_project_total_presentation", None),
        mc_run=result,
    )
    if live is None:
        return
    try:
        workflow.apply_variant_live_run(live)
    except ValueError:
        pass


def _put_mc_into_compare_slot(
    window: Any,
    workflow: ScenarioWorkflowService,
    slot_key: str,
    result: MCRunResult,
) -> None:
    from rcm_desktop.adapter.scenario_workflow_binding import capture_live_run_snapshot

    session = window._project_session()
    if session is None:
        return
    project = wss.editing_project(session)
    p50_run = build_run_result_from_mc_p50(project, result)
    snapshot = window.workspace_state.snapshot()
    live = LiveRunSnapshot(
        run_mode=RunMode.MONTE_CARLO,
        run_result=p50_run,
        mc_run=result,
        overlay=snapshot.planning_overlay,
        scenario_key=window.compare_scenario_combo.currentData(),
        presentation=getattr(window, "_project_total_presentation", None),
    )
    if slot_key == COMPARE_SLOT_A:
        workflow.freeze_live_as_scenario_1(live)
    else:
        workflow.put_scenario_2(live)


def _on_run_mode_changed(window: Any) -> None:
    refresh_simulation_status(window)
    window._rerender_detail_for_current_scope()


def _on_simulation_state_changed(window: Any, state: str) -> None:
    if state == "cancelled":
        store = ensure_simulation_store(window)
        detach_mc_run(store)
        window._state.set_last_mc_run(None)
        _clear_pending_mc_compare_slot(window)
    elif state == "error":
        _clear_pending_mc_compare_slot(window)
    refresh_simulation_status(window)
    window._update_run_buttons_enabled()
    if state == "idle":
        window._update_run_button_label()
    if state in {"cancelled", "done", "error"}:
        window._rerender_detail_for_current_scope()
