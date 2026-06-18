"""Taakgroep-catalogus + reverse index voor FM-editor (slice 59.4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rcm_core.editing.validation import normalize_key
from rcm_core.models import RCMProject

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.fm_edit_bundle_service import _edit_current


@dataclass(frozen=True)
class TaskGroupCatalogEntry:
    group_id: str
    omschrijving: str
    interval_jaar: float
    cost_eur: float
    fm_ids: tuple[str, ...]


def _pm_rows(source: RCMProject | EditingSession) -> list[dict[str, Any]]:
    if isinstance(source, EditingSession):
        return list(_edit_current(source).get("pm_tasks", []))
    return [
        {
            "pm_id": pm.pm_id,
            "fm_id": pm.fm_id,
            "task_group_id": pm.task_group_id,
            "taak_omschrijving": pm.taak_omschrijving,
        }
        for pm in source.pm_tasks.values()
    ]


def _group_rows(source: RCMProject | EditingSession) -> list[dict[str, Any]]:
    if isinstance(source, EditingSession):
        return list(_edit_current(source).get("task_groups", []))
    return [group.to_dict() for group in source.task_groups.values()]


def fms_for_group(source: RCMProject | EditingSession, group_id: str) -> tuple[str, ...]:
    target = normalize_key(group_id)
    fm_ids: set[str] = set()
    for row in _pm_rows(source):
        if normalize_key(row.get("task_group_id")) != target:
            continue
        fm_id = normalize_key(row.get("fm_id"))
        if fm_id:
            fm_ids.add(fm_id)
    return tuple(sorted(fm_ids))


def list_task_groups(source: RCMProject | EditingSession) -> tuple[TaskGroupCatalogEntry, ...]:
    groups = {normalize_key(r.get("group_id")): r for r in _group_rows(source) if normalize_key(r.get("group_id"))}
    entries: list[TaskGroupCatalogEntry] = []
    for group_id in sorted(groups):
        row = groups[group_id]
        fm_ids = fms_for_group(source, group_id)
        sample_pm = next(
            (pm for pm in _pm_rows(source) if normalize_key(pm.get("task_group_id")) == group_id),
            None,
        )
        omschrijving = str(sample_pm.get("taak_omschrijving") if sample_pm else row.get("omschrijving") or "")
        entries.append(
            TaskGroupCatalogEntry(
                group_id=group_id,
                omschrijving=omschrijving,
                interval_jaar=float(row.get("interval_jaar") or 0.0),
                cost_eur=float(row.get("cost_eur") or 0.0),
                fm_ids=fm_ids,
            )
        )
    return tuple(entries)


def allocate_task_group_id(source: RCMProject | EditingSession) -> str:
    used = {normalize_key(r.get("group_id")) for r in _group_rows(source)}
    n = 1
    while True:
        candidate = f"TG-{n:03d}"
        if candidate not in used:
            return candidate
        n += 1

