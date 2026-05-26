"""Async FM-editor commit via achtergrondthread (slice 47)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.fm_edit_commit_service import FmEditCommitResult, commit_edits
from rcm_desktop.adapter.qt.background_runner import BackgroundRunner


class _FmEditCommitWorker(QObject):
    finished = Signal(object)

    def __init__(
        self,
        session: EditingSession,
        *,
        project_path: str | Path | None,
        save_to_disk: bool,
        baseline_mtime_ns: int | None,
    ) -> None:
        super().__init__()
        self._session = session
        self._project_path = project_path
        self._save_to_disk = save_to_disk
        self._baseline_mtime_ns = baseline_mtime_ns

    @Slot()
    def run(self) -> None:
        result = commit_edits(
            self._session,
            project_path=self._project_path,
            save_to_disk=self._save_to_disk,
            baseline_mtime_ns=self._baseline_mtime_ns,
        )
        self.finished.emit(result)


class FmEditCommitRunner(QObject):
    finished = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._background = BackgroundRunner(self, lambda _state: None)

    @property
    def busy(self) -> bool:
        return self._background.busy

    def start(
        self,
        session: EditingSession,
        *,
        project_path: str | Path | None = None,
        save_to_disk: bool = False,
        baseline_mtime_ns: int | None = None,
    ) -> bool:
        if self._background.busy:
            return False
        worker = _FmEditCommitWorker(
            session,
            project_path=project_path,
            save_to_disk=save_to_disk,
            baseline_mtime_ns=baseline_mtime_ns,
        )
        return self._background.start(worker, on_finished=self._on_finished)

    @Slot(object)
    def _on_finished(self, result: object) -> None:
        self.finished.emit(result)
