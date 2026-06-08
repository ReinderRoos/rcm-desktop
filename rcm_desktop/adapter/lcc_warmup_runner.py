"""Background LCC curve warmup in render index (slice 38)."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from rcm_desktop.adapter.lcc_render_cache_service import build_lcc_curve_cache_key
from rcm_desktop.adapter.presentation_lazy_service import warm_lcc_render_index
from rcm_desktop.adapter.qt.background_runner import BackgroundRunner
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
        self._background = BackgroundRunner(self, self.state_changed.emit)

    @property
    def busy(self) -> bool:
        return self._background.busy

    def start(
        self,
        project: object,
        run: object,
        render_index: WorkspaceRenderIndex,
        snapshot: WorkspaceStateSnapshot,
    ) -> bool:
        if self._background.busy:
            return False
        if not isinstance(run, RunResult) or run.status != "done":
            return False
        worker = _LCCWarmupWorker(project, run, render_index, snapshot)
        return self._background.start(worker, on_finished=self._on_worker_finished)

    @Slot()
    def _on_worker_finished(self) -> None:
        self.state_changed.emit("done")
