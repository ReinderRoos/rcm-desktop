"""Background rebuild van presentatie-cache (slice 26)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot

from rcm_desktop.adapter.presentation_cache_service import (
    PresentationProjectTotal,
    attach_presentation_to_cache,
    build_project_total_presentation,
)
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
        dto = build_project_total_presentation(self._project, self._run)
        attach_presentation_to_cache(Path(self._project_path), self._project, dto)
        self.finished.emit(dto)


class PresentationRebuildRunner(QObject):
    state_changed = Signal(str)
    result_ready = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: _PresentationRebuildWorker | None = None
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def start(self, project: object, project_path: str, run: object) -> bool:
        if self._busy:
            return False
        self._busy = True
        self.state_changed.emit("busy")
        self._thread = QThread()
        self._worker = _PresentationRebuildWorker(project, project_path, run)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup)
        self._thread.start()
        return True

    @Slot(object)
    def _on_worker_finished(self, dto: object) -> None:
        self.result_ready.emit(dto)
        self.state_changed.emit("done" if dto is not None else "error")

    @Slot()
    def _cleanup(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None
        self._busy = False
        self.state_changed.emit("idle")
