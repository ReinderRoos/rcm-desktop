"""Slice 95 issues 11-12 — Monte Carlo run-modus minimal tracer."""

from __future__ import annotations

from rcm_desktop.adapter.simulation_job_service import (
    RunMode,
    SimulationJob,
    SimulationResultStore,
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
