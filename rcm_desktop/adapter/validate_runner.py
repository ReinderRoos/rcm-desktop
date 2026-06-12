from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from rcm_desktop.adapter import preview_service
from rcm_desktop.adapter import validate_service
from rcm_desktop.adapter.validate_service import DetailItem, UserFacingError, ValidateResult
from rcm_desktop.adapter.qt.background_runner import BackgroundRunner


class _ValidateWorker(QObject):
    finished = Signal(object, object, object)

    def __init__(self, project_path: str) -> None:
        super().__init__()
        self._project_path = project_path

    @Slot()
    def run(self) -> None:
        try:
            result, project = validate_service.run(self._project_path)
        except Exception as exc:
            result = ValidateResult(
                status="error",
                summary="Onverwachte fout tijdens valideren.",
                details=[
                    DetailItem(
                        severity="error",
                        code="VALIDATE_UNEXPECTED",
                        message=str(exc),
                    )
                ],
                error=UserFacingError(
                    code="UNEXPECTED_ERROR",
                    message="Er ging iets mis tijdens valideren.",
                ),
            )
            self.finished.emit(result, None, None)
            return
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
        self._background = BackgroundRunner(self, self.state_changed.emit)

    @property
    def busy(self) -> bool:
        return self._background.busy

    def start(self, project_path: str) -> bool:
        worker = _ValidateWorker(project_path)
        return self._background.start(worker, on_finished=self._on_worker_finished)

    @Slot(object, object, object)
    def _on_worker_finished(self, result: object, preview: object, project: object) -> None:
        self.result_ready.emit(result)
        self.preview_ready.emit(preview)
        self.project_ready.emit(project)
        status = getattr(result, "status", "error")
        self.state_changed.emit("done" if status in {"valid", "valid_with_warnings"} else "error")
