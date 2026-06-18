"""Slice 95 issues 11-12 — Monte Carlo run-modus minimal tracer."""

from __future__ import annotations

import pytest

from rcm_desktop.adapter.simulation_job_service import (
    RunMode,
    SimulationJob,
    SimulationResultStore,
    build_simulation_presentation,
    create_simulation_job,
)


def test_run_mode_default_analytical() -> None:
    assert RunMode.ANALYTICAL.value == "analytical"


def test_simulation_job_lifecycle() -> None:
    job = create_simulation_job(seed=42, iterations=100)
    assert job.status == "pending"
    job = job.start()
    assert job.status == "running"
    job = job.complete()
    assert job.status == "done"


def test_result_store_separates_analytical_and_mc() -> None:
    store = SimulationResultStore()
    store.set_analytical_run_id("run-1")
    store.set_mc_job_id("mc-1")
    assert store.analytical_run_id == "run-1"
    assert store.mc_job_id == "mc-1"
    assert store.analytical_run_id != store.mc_job_id


def test_result_store_preserves_analytical_when_mc_set() -> None:
    store = SimulationResultStore()
    store.set_analytical_run_id("run-analytical")
    store.set_mc_job_id("mc-job")
    store.set_mc_job_id("mc-job-2")
    assert store.analytical_run_id == "run-analytical"
    assert store.mc_job_id == "mc-job-2"
    assert store.uses_separate_namespaces is True


def test_build_simulation_presentation_exposes_seed_progress_status() -> None:
    job = create_simulation_job(seed=42, iterations=100).start()
    store = SimulationResultStore()
    store.set_analytical_run_id("run-1")
    store.set_mc_job_id("mc-1")
    presentation = build_simulation_presentation(
        run_mode=RunMode.MONTE_CARLO,
        job=job,
        store=store,
    )
    assert presentation.run_mode is RunMode.MONTE_CARLO
    assert presentation.seed == 42
    assert presentation.progress == 0.0
    assert presentation.status == "running"
    assert "42" in presentation.status_label
    assert presentation.analytical_run_id == "run-1"
    assert presentation.mc_job_id == "mc-1"


def test_build_simulation_presentation_done_job_shows_full_progress() -> None:
    job = create_simulation_job(seed=7, iterations=50).start().complete()
    presentation = build_simulation_presentation(
        run_mode=RunMode.MONTE_CARLO,
        job=job,
    )
    assert presentation.progress == 1.0
    assert presentation.status == "done"


def test_workspace_mc_mode_shows_idle_label_without_stub_job(qtbot, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QMessageBox

    from rcm_desktop.adapter.simulation_job_service import RunMode
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    qtbot.addWidget(window)
    window.show()
    idx = window.simulation_run_mode_combo.findData(RunMode.MONTE_CARLO)
    window.simulation_run_mode_combo.setCurrentIndex(idx)
    assert window.simulation_status_label.isVisible()
    assert "niet gestart" in window.simulation_status_label.text().lower()
