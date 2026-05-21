from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QThread, Signal, Slot

from rcm_desktop.adapter import scenario_run_service
from rcm_desktop.adapter.scenario_compare_service import ScenarioCompareView, build_compare_view
from rcm_desktop.adapter.scenario_run_service import ScenarioRunPairResult


@dataclass(frozen=True)
class CompareFlowResult:
    """Vergelijk-paneel: KPI-view + ruwe scenario-resultaten voor LCC."""

    view: ScenarioCompareView
    pair: ScenarioRunPairResult


class _CompareWorker(QObject):
    finished = Signal(object)

    def __init__(self, project: object, project_path: str) -> None:
        super().__init__()
        self._project = project
        self._project_path = project_path

    @Slot()
    def run(self) -> None:
        pair = scenario_run_service.run_compare(self._project, self._project_path)
        view = build_compare_view(pair.cm_result, pair.pm_result)
        self.finished.emit(CompareFlowResult(view=view, pair=pair))


class CompareRunner(QObject):
    state_changed = Signal(str)
    result_ready = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: _CompareWorker | None = None
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def start(self, project: object, project_path: str) -> bool:
        if self._busy:
            return False
        self._busy = True
        self.state_changed.emit("busy")
        self._thread = QThread()
        self._worker = _CompareWorker(project, project_path)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup)
        self._thread.start()
        return True

    @Slot(object)
    def _on_worker_finished(self, result: object) -> None:
        self.result_ready.emit(result)
        if isinstance(result, CompareFlowResult):
            status = result.view.status
        else:
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

