from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.preview_service import ProjectPreview
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.validate_service import ValidateResult
from rcm_core.models import RCMProject


class AppState(QObject):
    result_changed = Signal(object)
    preview_changed = Signal(object)
    project_changed = Signal(object)
    run_changed = Signal(object)
    project_run_view_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._last_result: ValidateResult | None = None
        self._last_preview: ProjectPreview | None = None
        self._last_project: RCMProject | None = None
        self._loaded_project: LoadedProject | None = None
        self._last_run: RunResult | None = None
        self._project_session: ProjectSession | None = None

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
    def loaded_project(self) -> LoadedProject | None:
        return self._loaded_project

    @property
    def last_run(self) -> RunResult | None:
        return self._last_run

    @property
    def project_session(self) -> ProjectSession | None:
        return self._project_session

    def _sync_project_session(
        self,
        *,
        path: Path | str | None = None,
    ) -> None:
        if self._loaded_project is None:
            self._project_session = None
            return
        p = Path(path) if path is not None else (
            Path(self._loaded_project.project_id)
            if self._loaded_project.project_id not in {"local", ""}
            else None
        )
        if p is not None and not p.suffix:
            p = None
        self._project_session = ProjectSession.from_parts(
            self._loaded_project,
            path=p,
            run=self._last_run,
        )

    def set_last_result(self, result: ValidateResult) -> None:
        self._last_result = result
        self.result_changed.emit(result)

    def set_last_preview(self, preview: ProjectPreview | None) -> None:
        self._last_preview = preview
        self.preview_changed.emit(preview)

    def set_last_project(self, project: RCMProject | None, *, path: Path | str | None = None) -> None:
        self._last_project = project
        if project is None:
            self._loaded_project = None
            self._project_session = None
        else:
            p = Path(path) if path is not None else None
            self._loaded_project = LoadedProject.from_core(project, path=p)
            self._sync_project_session(path=path)
        self.project_changed.emit(project)

    def set_last_run(self, result: RunResult | None) -> None:
        self._last_run = result
        if self._loaded_project is not None:
            self._sync_project_session()
        self.run_changed.emit(result)

    def set_last_project_and_run(
        self,
        project: RCMProject | None,
        run: RunResult | None,
        *,
        path: Path | str | None = None,
    ) -> None:
        """Atomische update voor project+run views (één signal)."""
        self._last_project = project
        self._last_run = run
        if project is None:
            self._loaded_project = None
            self._project_session = None
        else:
            p = Path(path) if path is not None else None
            self._loaded_project = LoadedProject.from_core(project, path=p)
            self._sync_project_session(path=path)
        self.project_run_view_changed.emit()
