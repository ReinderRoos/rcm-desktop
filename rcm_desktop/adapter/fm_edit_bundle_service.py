"""Laadt één FM-scope voor de faalwijze-editor (Qt-vrij)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rcm_core.editing.validation import normalize_key
from rcm_core.models import RCMProject

from rcm_desktop.adapter.editing_session import EditingSession


@dataclass(frozen=True)
class FmEditBundle:
    fm_id: str
    faalwijze_row: dict[str, Any]
    pbs_row: dict[str, Any]
    fm_effect_rows: tuple[dict[str, Any], ...]
    pm_task_rows: tuple[dict[str, Any], ...]
    pm_effect_rows: tuple[dict[str, Any], ...]
    task_group_rows: tuple[dict[str, Any], ...]
    effect_klasse_rows: tuple[dict[str, Any], ...]


def _edit_current(session: EditingSession | dict[str, Any]) -> dict[str, Any]:
    if isinstance(session, EditingSession):
        return session.session.get("edit_current", {})
    return session.get("edit_current", {})


def count_faalwijzen_for_pbs(project: RCMProject, pbs_id: str) -> int:
    target = normalize_key(pbs_id)
    return sum(1 for fm in project.faalwijzes.values() if normalize_key(fm.pbs_id) == target)


def count_faalwijzen_for_pbs_in_edit(session: EditingSession | dict[str, Any], pbs_id: str) -> int:
    target = normalize_key(pbs_id)
    rows = _edit_current(session).get("faalwijzes", [])
    return sum(1 for row in rows if normalize_key(row.get("pbs_id")) == target)


def count_faalwijzen_for_task_group(project: RCMProject, group_id: str) -> int:
    return _count_faalwijzen_for_task_group_pm_rows(
        [
            {
                "pm_id": pm.pm_id,
                "fm_id": pm.fm_id,
                "task_group_id": pm.task_group_id,
            }
            for pm in project.pm_tasks.values()
        ],
        group_id,
    )


def count_faalwijzen_for_task_group_in_edit(
    session: EditingSession | dict[str, Any], group_id: str
) -> int:
    pm_rows = _edit_current(session).get("pm_tasks", [])
    return _count_faalwijzen_for_task_group_pm_rows(pm_rows, group_id)


def _count_faalwijzen_for_task_group_pm_rows(
    pm_rows: list[dict[str, Any]], group_id: str
) -> int:
    target = normalize_key(group_id)
    if not target:
        return 0
    fm_ids: set[str] = set()
    for row in pm_rows:
        if normalize_key(row.get("task_group_id")) != target:
            continue
        fm_id = normalize_key(row.get("fm_id"))
        if fm_id:
            fm_ids.add(fm_id)
    return len(fm_ids)


def load_bundle_from_session(session: EditingSession, fm_id: str) -> FmEditBundle:
    """Compat: gebruik ``load_fm_edit_scope``."""
    from rcm_desktop.adapter.fm_edit_scope_loader import load_fm_edit_scope

    return load_fm_edit_scope(session, fm_id)


def load_bundle(project: RCMProject, fm_id: str) -> FmEditBundle:
    """Compat: gebruik ``load_fm_edit_scope``."""
    from rcm_desktop.adapter.fm_edit_scope_loader import load_fm_edit_scope

    return load_fm_edit_scope(project, fm_id)
