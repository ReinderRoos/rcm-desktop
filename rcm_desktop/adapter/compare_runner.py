from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, Slot

from rcm_desktop.adapter import scenario_run_service
from rcm_desktop.adapter.qt.background_runner import BackgroundRunner
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
        self._background = BackgroundRunner(self, self.state_changed.emit)

    @property
    def busy(self) -> bool:
        return self._background.busy

    def start(self, project: object, project_path: str) -> bool:
        worker = _CompareWorker(project, project_path)
        return self._background.start(worker, on_finished=self._on_worker_finished)

    @Slot(object)
    def _on_worker_finished(self, result: object) -> None:
        self.result_ready.emit(result)
        if isinstance(result, CompareFlowResult):
            status = result.view.status
        else:
            status = getattr(result, "status", "error")
        self.state_changed.emit("done" if status == "done" else "error")
