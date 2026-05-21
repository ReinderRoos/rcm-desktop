"""Qt-run-runner: motor + presentatie-cache op achtergrondthread."""
from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal, Slot

from rcm_desktop.adapter import run_service
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.presentation_cache_service import (
    PresentationProjectTotal,
    attach_presentation_to_cache,
    build_project_total_presentation,
)

PHASE_MOTOR = "motor"
PHASE_PRESENTATION = "presentation"


class _RunWorker(QObject):
    finished = Signal(object, object)

    def __init__(
        self,
        project: object,
        project_path: str,
        planning_overlay: PlanningOverlayState | None,
    ) -> None:
        super().__init__()
        self._project = project
        self._project_path = project_path
        self._planning_overlay = planning_overlay

    @Slot()
    def run(self) -> None:
        result = run_service.run(
            self._project,
            self._project_path,
            full_recompute=True,
            parallel=False,
            planning_overlay=self._planning_overlay,
        )
        presentation = None
        if result.status == "done":
            presentation = build_project_total_presentation(self._project, result)
            attach_presentation_to_cache(
                self._project_path, self._project, presentation
            )
        self.finished.emit(result, presentation)


class RunRunner(QObject):
    state_changed = Signal(str)
    phase_changed = Signal(str)
    result_ready = Signal(object, object)

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: _RunWorker | None = None
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def start(
        self,
        project: object,
        project_path: str,
        *,
        planning_overlay: PlanningOverlayState | None = None,
    ) -> bool:
        if self._busy:
            return False

        self._busy = True
        self.state_changed.emit("busy")
        self.phase_changed.emit(PHASE_MOTOR)

        self._thread = QThread()
        self._worker = _RunWorker(project, project_path, planning_overlay)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup)
        self._thread.start()
        return True

    @Slot(object, object)
    def _on_worker_finished(self, result: object, presentation: object) -> None:
        if getattr(result, "status", None) == "done":
            self.phase_changed.emit(PHASE_PRESENTATION)
        self.result_ready.emit(result, presentation)
        status = getattr(result, "status", "error")
        self.state_changed.emit("done" if status == "done" else "error")

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
