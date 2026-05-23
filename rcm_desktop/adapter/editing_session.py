"""EditingSession — tabulaire editing-pipeline seam voor alle materialisatie-paden."""

from __future__ import annotations

import copy
from typing import Any

from rcm_core.editing.persistence import build_project_from_state
from rcm_core.editing.state import apply_rows, init_edit_state, validate_all_entities
from rcm_core.models import RCMProject


class EditingSession:
    """Beheert injecteerbare edit-sessie (`session=dict`) voor adapter."""

    def __init__(self, *, session: dict[str, Any] | None = None) -> None:
        self._session = session if session is not None else {}
        self._base_project: RCMProject | None = None

    @property
    def session(self) -> dict[str, Any]:
        return self._session

    def load_project(self, project: RCMProject) -> None:
        self._base_project = project
        init_edit_state(project, session=self._session)

    def apply_entity_rows(self, entity: str, rows: list[dict[str, Any]]) -> None:
        apply_rows(entity, rows, session=self._session)

    def validate(self) -> dict[str, list[str]]:
        return validate_all_entities(session=self._session)

    def build_project(self) -> RCMProject:
        if self._base_project is None:
            raise ValueError("Geen project geladen in EditingSession.")
        return build_project_from_state(self._base_project, session=self._session)

    def clone_with_project(self, project: RCMProject) -> EditingSession:
        cloned = copy.deepcopy(project)
        out = EditingSession()
        out.load_project(cloned)
        return out
