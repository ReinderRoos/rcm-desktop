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

    def start(self) -> SimulationJob:
        return SimulationJob(seed=self.seed, iterations=self.iterations, status="running")

    def complete(self) -> SimulationJob:
        return SimulationJob(seed=self.seed, iterations=self.iterations, status="done")

    def cancel(self) -> SimulationJob:
        return SimulationJob(seed=self.seed, iterations=self.iterations, status="cancelled")


def create_simulation_job(*, seed: int, iterations: int) -> SimulationJob:
    return SimulationJob(seed=seed, iterations=iterations, status="pending")


@dataclass
class SimulationResultStore:
    analytical_run_id: str | None = None
    mc_job_id: str | None = None

    def set_analytical_run_id(self, run_id: str) -> None:
        self.analytical_run_id = run_id

    def set_mc_job_id(self, job_id: str) -> None:
        self.mc_job_id = job_id
