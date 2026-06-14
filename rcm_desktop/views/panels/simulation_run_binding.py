"""Start-analyse dispatch for analytical vs Monte Carlo (slice 98 issue 06)."""

from __future__ import annotations

from typing import Any

from rcm_desktop.adapter import workspace_session_service as wss
from rcm_desktop.adapter.simulation_engine_service import MCRunResult, attach_mc_run_to_store, detach_mc_run
from rcm_desktop.adapter.simulation_runner import SimulationRunner
from rcm_desktop.adapter.simulation_workspace_service import (
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
        return _start_monte_carlo(window, session)
    return _start_analytical(window, session)


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
        window.run_analyse_button.setEnabled(False)
        return True
    return False


def _start_monte_carlo(window: Any, session: Any) -> bool:
    runner = ensure_simulation_runner(window)
    project = wss.editing_project(session)
    params = monte_carlo_params_from_project(project)
    if runner.start(project, n=params.n, seed=params.seed):
        window.run_analyse_button.setEnabled(False)
        return True
    return False


def _on_simulation_job_changed(window: Any, job: object) -> None:
    window._simulation_job = job
    refresh_simulation_status(window)


def _on_mc_result_ready(window: Any, result: object) -> None:
    if not isinstance(result, MCRunResult):
        return
    store = ensure_simulation_store(window)
    attach_mc_run_to_store(store, result, job_id=f"mc-{result.seed}-{result.n_completed}")
    window._state.set_last_mc_run(result)
    refresh_simulation_status(window)
    window._rerender_detail_for_current_scope()


def _on_run_mode_changed(window: Any) -> None:
    refresh_simulation_status(window)
    window._rerender_detail_for_current_scope()


def _on_simulation_state_changed(window: Any, state: str) -> None:
    if state == "cancelled":
        store = ensure_simulation_store(window)
        detach_mc_run(store)
        window._state.set_last_mc_run(None)
    refresh_simulation_status(window)
    window._update_run_buttons_enabled()
    if state in {"cancelled", "done", "error"}:
        window._rerender_detail_for_current_scope()
