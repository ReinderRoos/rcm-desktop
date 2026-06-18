"""Qt-run-runner: motor + presentatie-cache op achtergrondthread."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from rcm_desktop.adapter import run_service
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.presentation_cache_service import (
    attach_presentation_to_cache,
    build_contribution_presentation,
)
from rcm_desktop.adapter.qt.background_runner import BackgroundRunner
from rcm_desktop.adapter.run_policy import DEFAULT_RUN_POLICY, RunUserIntent

PHASE_MOTOR = "motor"
PHASE_PRESENTATION = "presentation"


class _RunWorker(QObject):
    finished = Signal(object, object)

    def __init__(
        self,
        project: object,
        project_path: str,
        planning_overlay: PlanningOverlayState | None,
        *,
        force_recompute: bool,
    ) -> None:
        super().__init__()
        self._project = project
        self._project_path = project_path
        self._planning_overlay = planning_overlay
        self._force_recompute = force_recompute

    @Slot()
    def run(self) -> None:
        intent = (
            RunUserIntent.FORCE_RECOMPUTE
            if self._force_recompute
            else RunUserIntent.START_ANALYSE
        )
        opts = DEFAULT_RUN_POLICY.resolve(user_intent=intent)
        result = run_service.run(
            self._project,
            self._project_path,
            full_recompute=opts.full_recompute,
            parallel=opts.parallel,
            planning_overlay=self._planning_overlay,
        )
        presentation = None
        if result.status == "done":
            presentation = build_contribution_presentation(self._project, result)
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
        self._background = BackgroundRunner(self, self.state_changed.emit)

    @property
    def busy(self) -> bool:
        return self._background.busy

    def start(
        self,
        project: object,
        project_path: str,
        *,
        planning_overlay: PlanningOverlayState | None = None,
        force_recompute: bool = False,
    ) -> bool:
        if self._background.busy:
            return False

        self.phase_changed.emit(PHASE_MOTOR)
        worker = _RunWorker(
            project,
            project_path,
            planning_overlay,
            force_recompute=force_recompute,
        )
        return self._background.start(worker, on_finished=self._on_worker_finished)

    @Slot(object, object)
    def _on_worker_finished(self, result: object, presentation: object) -> None:
        if getattr(result, "status", None) == "done":
            self.phase_changed.emit(PHASE_PRESENTATION)
        self.result_ready.emit(result, presentation)
        status = getattr(result, "status", "error")
        self.state_changed.emit("done" if status == "done" else "error")
