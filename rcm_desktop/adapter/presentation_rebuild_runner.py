"""Background rebuild van presentatie-cache (slice 26)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from rcm_desktop.adapter.presentation_cache_service import (
    attach_presentation_to_cache,
    build_contribution_presentation,
)
from rcm_desktop.adapter.qt.background_runner import BackgroundRunner
from rcm_desktop.adapter.run_service import RunResult


class _PresentationRebuildWorker(QObject):
    finished = Signal(object)

    def __init__(self, project: object, project_path: str, run: object) -> None:
        super().__init__()
        self._project = project
        self._project_path = project_path
        self._run = run

    @Slot()
    def run(self) -> None:
        if not isinstance(self._run, RunResult) or self._run.status != "done":
            self.finished.emit(None)
            return
        dto = build_contribution_presentation(self._project, self._run)
        attach_presentation_to_cache(Path(self._project_path), self._project, dto)
        self.finished.emit(dto)


class PresentationRebuildRunner(QObject):
    state_changed = Signal(str)
    result_ready = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._background = BackgroundRunner(self, self.state_changed.emit)

    @property
    def busy(self) -> bool:
        return self._background.busy

    def start(self, project: object, project_path: str, run: object) -> bool:
        worker = _PresentationRebuildWorker(project, project_path, run)
        return self._background.start(worker, on_finished=self._on_worker_finished)

    @Slot(object)
    def _on_worker_finished(self, dto: object) -> None:
        self.result_ready.emit(dto)
        self.state_changed.emit("done" if dto is not None else "error")
