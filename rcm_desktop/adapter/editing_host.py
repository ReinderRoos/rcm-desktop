"""Expliciete host voor gedeelde FM-edit buffer en tabulaire edit-service (slice 46-08)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from rcm_core.models import RCMProject

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.entity_edit_service import EntityEditService
from rcm_desktop.adapter.fm_edit_commit_facade import commit_fm_edit
from rcm_desktop.adapter.fm_edit_commit_service import FmEditCommitResult

_process_host: EditingHost | None = None

_FAALWIJZEN_VIEW = "input.faalwijzen"


class EditingHost:
    """Project-brede edit-buffer: één grid-service, één EditingSession, gedeelde commit."""

    def __init__(self) -> None:
        self._grid: EntityEditService | None = None
        self._save_handler: Callable[[], bool] | None = None

    @property
    def editing_session(self) -> EditingSession:
        grid = self.grid_service()
        if grid is None:
            raise RuntimeError("Geen actieve tabulaire edit-service op EditingHost")
        return grid.editing_session

    def grid_service(self) -> EntityEditService | None:
        if self._grid is None or not self._grid.is_active():
            return None
        return self._grid

    def ensure_grid(self, project: RCMProject) -> EntityEditService:
        grid = self.grid_service()
        if grid is None:
            grid = EntityEditService.for_view(_FAALWIJZEN_VIEW)
            grid.reset(project)
            self._grid = grid
        return grid

    def attach_grid(self, service: EntityEditService | None) -> None:
        self._grid = service

    def is_grid_dirty(self) -> bool:
        """Buffer-brede dirty-check: `edit_dirty_global` uit de editing-pipeline (slice 89)."""
        grid = self.grid_service()
        if grid is None:
            return False
        session = grid.editing_session.session
        return bool(session.get("edit_dirty_global", False))

    def discard_buffer_changes(self) -> None:
        """Verwerp onopgeslagen invoerwijzigingen buffer-breed (slice 89)."""
        grid = self.grid_service()
        if grid is None:
            return
        from rcm_core.editing.state import restore_entity

        session = grid.editing_session.session
        for entity, dirty in dict(session.get("edit_dirty", {})).items():
            if dirty:
                restore_entity(entity, session=session)
        grid.discard_changes()

    def set_save_handler(self, handler: Callable[[], bool] | None) -> None:
        self._save_handler = handler

    def swap_save_handler(
        self, handler: Callable[[], bool] | None
    ) -> Callable[[], bool] | None:
        previous = self._save_handler
        self._save_handler = handler
        return previous

    def invoke_grid_save(self) -> bool:
        if self._save_handler is not None:
            return self._save_handler()
        grid = self.grid_service()
        if grid is None or not grid.is_active():
            return True
        if grid.has_errors():
            return False
        return self.commit_grid_edits().ok

    def clear_grid(self) -> None:
        if self._grid is not None:
            self._grid.clear()
        self._grid = None
        self._save_handler = None

    def commit_grid_edits(
        self,
        *,
        path: Path | str | None = None,
        save_to_disk: bool = False,
        baseline_mtime_ns: int | None = None,
    ) -> FmEditCommitResult:
        session = self.editing_session
        result = commit_fm_edit(
            session,
            None,
            path=path,
            save_to_disk=save_to_disk,
            baseline_mtime_ns=baseline_mtime_ns,
        )
        if result.ok and result.project is not None:
            session.load_project(result.project)
        return result


def get_editing_host() -> EditingHost:
    global _process_host
    if _process_host is None:
        _process_host = EditingHost()
    return _process_host


def reset_editing_host_for_tests() -> None:
    """Test-seam: leeg process-wide host."""
    global _process_host
    _process_host = EditingHost()
