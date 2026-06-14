"""Qt SimulationRunner for Monte Carlo jobs (slice 98 issue 05)."""

from __future__ import annotations

import random

from PySide6.QtCore import QObject, Signal, Slot

from rcm_core.models import RCMProject
from rcm_desktop.adapter.qt.background_runner import BackgroundRunner
from rcm_desktop.adapter.simulation_engine_service import MCRunResult, run_monte_carlo
from rcm_desktop.adapter.simulation_job_service import SimulationJob, create_simulation_job


class _SimulationWorker(QObject):
    finished = Signal(object, object)
    progress_changed = Signal(float)
    job_changed = Signal(object)

    def __init__(
        self,
        project: RCMProject,
        *,
        n: int,
        seed: int | None,
    ) -> None:
        super().__init__()
        self._project = project
        self._n = n
        self._requested_seed = seed
        self._effective_seed = int(seed) if seed is not None else random.randint(0, 2**31 - 1)
        self._cancel_requested = False
        self._job = create_simulation_job(seed=self._effective_seed, iterations=n).start()

    def request_cancel(self) -> None:
        self._cancel_requested = True

    def _set_job(self, job: SimulationJob) -> None:
        self._job = job
        self.job_changed.emit(job)

    @Slot()
    def run(self) -> None:
        def progress_cb(completed: int, total: int) -> None:
            progress = completed / total if total else 0.0
            self._set_job(
                SimulationJob(
                    seed=self._effective_seed,
                    iterations=total,
                    status="running",
                    progress=progress,
                )
            )
            self.progress_changed.emit(progress)

        def cancel_check() -> bool:
            return self._cancel_requested

        run_seed = self._requested_seed if self._requested_seed is not None else self._effective_seed
        result = run_monte_carlo(
            self._project,
            n=self._n,
            seed=run_seed,
            progress_cb=progress_cb,
            cancel_check=cancel_check,
        )
        self._effective_seed = result.seed

        if result.status == "cancelled":
            self._set_job(self._job.cancel())
        elif result.status == "done":
            self._set_job(self._job.complete())
        else:
            self._set_job(
                SimulationJob(
                    seed=result.seed,
                    iterations=self._n,
                    status="error",
                    progress=self._job.progress,
                )
            )

        self.finished.emit(result, self._job)


class SimulationRunner(QObject):
    state_changed = Signal(str)
    progress_changed = Signal(float)
    job_changed = Signal(object)
    result_ready = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._background = BackgroundRunner(self, self._on_background_state)
        self._worker: _SimulationWorker | None = None
        self._active_job: SimulationJob | None = None

    @property
    def busy(self) -> bool:
        return self._background.busy

    @property
    def active_job(self) -> SimulationJob | None:
        return self._active_job

    def _on_background_state(self, state: str) -> None:
        if state == "idle" and self._active_job is not None:
            return
        self.state_changed.emit(state)

    def start(
        self,
        project: RCMProject,
        *,
        n: int,
        seed: int | None = None,
    ) -> bool:
        if self._background.busy:
            return False
        worker = _SimulationWorker(project, n=n, seed=seed)
        self._worker = worker
        worker.progress_changed.connect(self.progress_changed.emit)
        worker.job_changed.connect(self._on_job_changed)
        return self._background.start(worker, on_finished=self._on_worker_finished)

    def cancel(self) -> None:
        if self._worker is not None:
            self._worker.request_cancel()

    def _on_job_changed(self, job: object) -> None:
        if isinstance(job, SimulationJob):
            self._active_job = job
            self.job_changed.emit(job)

    @Slot(object, object)
    def _on_worker_finished(self, result: object, job: object) -> None:
        self._worker = None
        if isinstance(job, SimulationJob):
            self._active_job = job
            self.job_changed.emit(job)
        if isinstance(result, MCRunResult):
            if result.status == "done":
                self.result_ready.emit(result)
            terminal = {
                "done": "done",
                "cancelled": "cancelled",
            }.get(result.status, "error")
            self.state_changed.emit(terminal)
