"""Background LCC curve warmup in render index (slice 38)."""
from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal, Slot

from rcm_desktop.adapter.lcc_render_cache_service import build_lcc_curve_cache_key
from rcm_desktop.adapter.presentation_lazy_service import warm_lcc_render_index
from rcm_desktop.adapter.results_workspace_state import WorkspaceStateSnapshot
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.workspace_render_index import WorkspaceRenderIndex


class _LCCWarmupWorker(QObject):
    finished = Signal()

    def __init__(
        self,
        project: object,
        run: object,
        render_index: WorkspaceRenderIndex,
        snapshot: WorkspaceStateSnapshot,
    ) -> None:
        super().__init__()
        self._project = project
        self._run = run
        self._render_index = render_index
        self._snapshot = snapshot

    @Slot()
    def run(self) -> None:
        if not isinstance(self._run, RunResult) or self._run.status != "done":
            self.finished.emit()
            return
        warm_lcc_render_index(
            self._render_index,
            project=self._project,
            run=self._run,
            scope_id=self._snapshot.scope_id,
            cache_modus_key=build_lcc_curve_cache_key(self._snapshot),
            overlay=self._snapshot.planning_overlay,
            type_filters=self._snapshot.lcc_filters,
        )
        self.finished.emit()


class LCCWarmupRunner(QObject):
    state_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: _LCCWarmupWorker | None = None
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def start(
        self,
        project: object,
        run: object,
        render_index: WorkspaceRenderIndex,
        snapshot: WorkspaceStateSnapshot,
    ) -> bool:
        if self._busy:
            return False
        if not isinstance(run, RunResult) or run.status != "done":
            return False
        self._busy = True
        self.state_changed.emit("busy")
        self._thread = QThread()
        self._worker = _LCCWarmupWorker(project, run, render_index, snapshot)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._on_worker_finished)
        self._thread.finished.connect(self._cleanup)
        self._thread.start()
        return True

    @Slot()
    def _on_worker_finished(self) -> None:
        self.state_changed.emit("done")

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
