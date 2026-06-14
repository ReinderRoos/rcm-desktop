"""Slice 98 issue 05 — SimulationRunner + cancel (pytest-qt)."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from rcm_core.config import RCMConfig
from rcm_core.models import FailureType, Faalwijze, Functie, PBSItem, RCMProject
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.simulation_engine_service import MCRunResult, MetricBand
from rcm_desktop.adapter.simulation_job_service import (
    RunMode,
    SimulationJob,
    build_simulation_presentation,
    create_simulation_job,
)
from rcm_desktop.adapter.simulation_runner import SimulationRunner
from rcm_desktop.app_state import AppState


def _ensure_app() -> QApplication | QCoreApplication:
    app = QApplication.instance() or QCoreApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _tiny_project() -> RCMProject:
    cfg = RCMConfig(lifecycle_years=80.0, modeljaar=2026, monte_carlo_n=500)
    pbs = PBSItem("PBS-1", "Obj", "El", "BD", bouwjaar=2000)
    func = Functie("F-1", "PBS-1", "Functie")
    fm = Faalwijze(
        "FM-R",
        "PBS-1",
        "F-1",
        "Random",
        failure_type=FailureType.RANDOM,
        mttf_jaar=10.0,
        cost_cm_eur=500.0,
    )
    return RCMProject(
        config=cfg,
        pbs_items={"PBS-1": pbs},
        functies={"F-1": func},
        faalwijzes={"FM-R": fm},
    )


@pytest.fixture
def qapp():
    return _ensure_app()


def test_simulation_runner_emits_progress_during_slow_run(qapp, monkeypatch):
    project = _tiny_project()
    progress_values: list[float] = []

    original = None

    def slow_run(*args, **kwargs):
        progress_cb = kwargs.get("progress_cb")
        for i in range(1, 6):
            if progress_cb is not None:
                progress_cb(i, 5)
            time.sleep(0.01)
        return MCRunResult(status="done", seed=11, n_completed=5)

    import rcm_desktop.adapter.simulation_runner as runner_mod

    monkeypatch.setattr(runner_mod, "run_monte_carlo", slow_run)

    runner = SimulationRunner()
    runner.progress_changed.connect(progress_values.append)
    assert runner.start(project, n=5, seed=11) is True

    while runner.busy:
        qapp.processEvents()

    assert any(p > 0.0 for p in progress_values)


def test_cancel_discards_result_and_clears_mc_slot(qapp, monkeypatch):
    project = _tiny_project()
    done_results: list[object] = []
    state = AppState()
    state.set_last_project(project)

    def slow_run(*args, **kwargs):
        progress_cb = kwargs.get("progress_cb")
        cancel_check = kwargs.get("cancel_check")
        for i in range(1, 51):
            if cancel_check is not None and cancel_check():
                return MCRunResult(status="cancelled", seed=3, n_completed=i - 1)
            if progress_cb is not None:
                progress_cb(i, 50)
            time.sleep(0.005)
        return MCRunResult(status="done", seed=3, n_completed=50)

    import rcm_desktop.adapter.simulation_runner as runner_mod

    monkeypatch.setattr(runner_mod, "run_monte_carlo", slow_run)

    runner = SimulationRunner()
    runner.result_ready.connect(done_results.append)
    assert runner.start(project, n=50, seed=3) is True
    runner.cancel()

    while runner.busy:
        qapp.processEvents()

    assert done_results == []
    state.set_last_mc_run(None)
    session = state.project_session
    assert session is not None
    assert session.mc_run is None


def test_busy_guard_blocks_second_start(qapp, monkeypatch):
    project = _tiny_project()
    started = {"n": 0}

    def blocking_run(*_a, **_k):
        started["n"] += 1
        time.sleep(0.05)
        return MCRunResult(status="done", seed=1, n_completed=10)

    import rcm_desktop.adapter.simulation_runner as runner_mod

    monkeypatch.setattr(runner_mod, "run_monte_carlo", blocking_run)

    runner = SimulationRunner()
    assert runner.start(project, n=10, seed=1) is True
    assert runner.start(project, n=10, seed=1) is False

    while runner.busy:
        qapp.processEvents()

    assert started["n"] == 1


def test_build_simulation_presentation_cancelled_shows_seed_and_progress():
    job = create_simulation_job(seed=99, iterations=100).start()
    job = SimulationJob(
        seed=job.seed,
        iterations=job.iterations,
        status="cancelled",
        progress=0.42,
    )
    presentation = build_simulation_presentation(
        run_mode=RunMode.MONTE_CARLO,
        job=job,
    )
    assert presentation.status == "cancelled"
    assert presentation.seed == 99
    assert "99" in presentation.status_label
    assert "42" in presentation.status_label or "geannuleerd" in presentation.status_label.lower()


def test_cancel_recovery_analytical_run_still_works(qapp):
    state = AppState()
    project = _tiny_project()
    analytical = RunResult(
        status="done",
        summary="analytical",
        metrics=RunMetrics(
            fm_result_count=1,
            total_lifecycle_faalmomenten=1.0,
            total_cost_eur=1.0,
        ),
    )
    state.set_last_project_and_run(project, analytical)
    state.set_last_mc_run(None)

    session = state.project_session
    assert session is not None
    assert session.run is analytical
    assert session.mc_run is None
