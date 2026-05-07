from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal, Slot

from rcm_desktop.adapter import preview_service
from rcm_desktop.adapter import validate_service


class _ValidateWorker(QObject):
    finished = Signal(object, object, object)

    def __init__(self, project_path: str) -> None:
        super().__init__()
        self._project_path = project_path

    @Slot()
    def run(self) -> None:
        result, project = validate_service.run(self._project_path)
        preview = None
        if result.status in {"valid", "valid_with_warnings"} and project is not None:
            preview = preview_service.build(project)
        exposed_project = project if result.status in {"valid", "valid_with_warnings"} else None
        self.finished.emit(result, preview, exposed_project)


class ValidateRunner(QObject):
    state_changed = Signal(str)
    result_ready = Signal(object)
    preview_ready = Signal(object)
    project_ready = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: _ValidateWorker | None = None
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def start(self, project_path: str) -> bool:
        if self._busy:
            return False

        self._busy = True
        self.state_changed.emit("busy")

        self._thread = QThread()
        self._worker = _ValidateWorker(project_path)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup)
        self._thread.start()
        return True

    @Slot(object, object, object)
    def _on_worker_finished(self, result: object, preview: object, project: object) -> None:
        self.result_ready.emit(result)
        self.preview_ready.emit(preview)
        self.project_ready.emit(project)
        status = getattr(result, "status", "error")
        self.state_changed.emit("done" if status in {"valid", "valid_with_warnings"} else "error")

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
