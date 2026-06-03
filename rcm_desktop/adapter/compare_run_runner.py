"""Qt runner for one A/B slot motor run (slice 56)."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from rcm_desktop.adapter.compare_run_config import CompareRunConfig
from rcm_desktop.adapter.compare_run_service import CompareRunOutcome, CompareRunService
from rcm_desktop.adapter.qt.background_runner import BackgroundRunner


class _CompareSlotWorker(QObject):
    finished = Signal(object)

    def __init__(
        self,
        project: object,
        project_path: str,
        slot_key: str,
        config: CompareRunConfig,
    ) -> None:
        super().__init__()
        self._project = project
        self._project_path = project_path
        self._slot_key = slot_key
        self._config = config

    @Slot()
    def run(self) -> None:
        outcome = CompareRunService.run_slot(
            self._project,
            self._project_path,
            self._config,
            slot_key=self._slot_key,
        )
        self.finished.emit(outcome)


class CompareRunRunner(QObject):
    state_changed = Signal(str)
    slot_result_ready = Signal(str, object)

    def __init__(self) -> None:
        super().__init__()
        self._background = BackgroundRunner(self, self.state_changed.emit)
        self._active_slot: str | None = None

    @property
    def busy(self) -> bool:
        return self._background.busy

    @property
    def active_slot(self) -> str | None:
        return self._active_slot

    def start(
        self,
        project: object,
        project_path: str,
        slot_key: str,
        config: CompareRunConfig,
    ) -> bool:
        if self._background.busy:
            return False
        self._active_slot = slot_key
        worker = _CompareSlotWorker(project, project_path, slot_key, config)
        return self._background.start(worker, on_finished=self._on_worker_finished)

    @Slot(object)
    def _on_worker_finished(self, outcome: object) -> None:
        slot = self._active_slot or "A"
        self._active_slot = None
        if isinstance(outcome, CompareRunOutcome):
            self.slot_result_ready.emit(slot, outcome)
        status = getattr(outcome, "status", "error")
        self.state_changed.emit("done" if status == "done" else "error")
