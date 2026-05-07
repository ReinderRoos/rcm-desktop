from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from rcm_desktop.adapter.preview_service import ProjectPreview
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.validate_service import ValidateResult
from rcm_core.models import RCMProject


class AppState(QObject):
    result_changed = Signal(object)
    preview_changed = Signal(object)
    project_changed = Signal(object)
    run_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._last_result: ValidateResult | None = None
        self._last_preview: ProjectPreview | None = None
        self._last_project: RCMProject | None = None
        self._last_run: RunResult | None = None

    @property
    def last_result(self) -> ValidateResult | None:
        return self._last_result

    @property
    def last_preview(self) -> ProjectPreview | None:
        return self._last_preview

    @property
    def last_project(self) -> RCMProject | None:
        return self._last_project

    @property
    def last_run(self) -> RunResult | None:
        return self._last_run

    def set_last_result(self, result: ValidateResult) -> None:
        self._last_result = result
        self.result_changed.emit(result)

    def set_last_preview(self, preview: ProjectPreview | None) -> None:
        self._last_preview = preview
        self.preview_changed.emit(preview)

    def set_last_project(self, project: RCMProject | None) -> None:
        self._last_project = project
        self.project_changed.emit(project)

    def set_last_run(self, result: RunResult | None) -> None:
        self._last_run = result
        self.run_changed.emit(result)
