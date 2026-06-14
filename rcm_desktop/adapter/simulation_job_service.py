"""Monte Carlo run-modus en job lifecycle stub (slice 95 issues 11-12)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RunMode(Enum):
    ANALYTICAL = "analytical"
    MONTE_CARLO = "monte_carlo"


@dataclass(frozen=True)
class SimulationJob:
    seed: int
    iterations: int
    status: str  # pending | running | done | cancelled
    progress: float = 0.0

    def start(self) -> SimulationJob:
        return SimulationJob(
            seed=self.seed,
            iterations=self.iterations,
            status="running",
            progress=0.0,
        )

    def complete(self) -> SimulationJob:
        return SimulationJob(
            seed=self.seed,
            iterations=self.iterations,
            status="done",
            progress=1.0,
        )

    def cancel(self) -> SimulationJob:
        return SimulationJob(
            seed=self.seed,
            iterations=self.iterations,
            status="cancelled",
            progress=self.progress,
        )


def create_simulation_job(*, seed: int, iterations: int) -> SimulationJob:
    return SimulationJob(seed=seed, iterations=iterations, status="pending")


@dataclass
class SimulationResultStore:
    analytical_run_id: str | None = None
    mc_job_id: str | None = None

    @property
    def uses_separate_namespaces(self) -> bool:
        """Analytische run en MC-job gebruiken gescheiden ID-slots (geen cache-conflict)."""
        return True

    def set_analytical_run_id(self, run_id: str) -> None:
        self.analytical_run_id = run_id

    def set_mc_job_id(self, job_id: str) -> None:
        self.mc_job_id = job_id


@dataclass(frozen=True)
class SimulationPresentation:
    run_mode: RunMode
    seed: int | None
    progress: float
    status: str
    status_label: str
    analytical_run_id: str | None = None
    mc_job_id: str | None = None


def build_simulation_presentation(
    *,
    run_mode: RunMode = RunMode.ANALYTICAL,
    job: SimulationJob | None = None,
    store: SimulationResultStore | None = None,
) -> SimulationPresentation:
    if job is None:
        seed: int | None = None
        progress = 0.0
        status = "idle"
        status_label = "Analytische run"
        if run_mode is RunMode.MONTE_CARLO:
            status_label = "Monte Carlo — niet gestart"
    else:
        seed = job.seed
        progress = job.progress
        status = job.status
        pct = int(progress * 100)
        if status == "cancelled":
            status_label = f"Monte Carlo seed {job.seed} — geannuleerd ({pct}%)"
        elif status == "done":
            status_label = f"Monte Carlo seed {job.seed} — voltooid ({pct}%)"
        else:
            status_label = f"Monte Carlo seed {job.seed} — {status} ({pct}%)"
        if run_mode is RunMode.ANALYTICAL:
            status_label = f"Analytische run — {status}"
    return SimulationPresentation(
        run_mode=run_mode,
        seed=seed,
        progress=progress,
        status=status,
        status_label=status_label,
        analytical_run_id=None if store is None else store.analytical_run_id,
        mc_job_id=None if store is None else store.mc_job_id,
    )
