"""Laadt één FM-scope voor de faalwijze-editor (Qt-vrij)."""

from __future__ import annotations

import copy
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
    """Laad FM-scope uit een actieve ``EditingSession`` (gedeelde grid/editor-buffer)."""
    if not session.is_loaded:
        raise RuntimeError("EditingSession is niet geladen")
    current = _edit_current(session)
    target = normalize_key(fm_id)
    faal_row = next(
        (r for r in current.get("faalwijzes", []) if normalize_key(r.get("fm_id")) == target),
        None,
    )
    if faal_row is None:
        raise KeyError(f"Onbekende faalwijze in sessie: {fm_id}")
    pbs_id = normalize_key(faal_row.get("pbs_id"))
    pbs_row = next(
        (r for r in current.get("pbs", []) if normalize_key(r.get("pbs_id")) == pbs_id),
        None,
    )
    if pbs_row is None:
        raise KeyError(f"PBS ontbreekt in sessie voor {fm_id}: {pbs_id}")

    fm_effect_rows = tuple(
        r for r in current.get("fm_effect_links", []) if normalize_key(r.get("fm_id")) == target
    )
    pm_task_rows = tuple(
        r for r in current.get("pm_tasks", []) if normalize_key(r.get("fm_id")) == target
    )
    pm_ids = {normalize_key(r.get("pm_id")) for r in pm_task_rows}
    pm_effect_rows = tuple(
        r for r in current.get("pm_effect_links", []) if normalize_key(r.get("pm_id")) in pm_ids
    )
    group_ids = {
        normalize_key(r.get("task_group_id"))
        for r in pm_task_rows
        if normalize_key(r.get("task_group_id"))
    }
    task_group_rows = tuple(
        r for r in current.get("task_groups", []) if normalize_key(r.get("group_id")) in group_ids
    )
    klasse_ids: set[str] = set()
    for row in fm_effect_rows + pm_effect_rows:
        kid = normalize_key(row.get("klasse_id"))
        if kid:
            klasse_ids.add(kid)
    effect_klasse_rows = tuple(
        r for r in current.get("effect_klassen", []) if normalize_key(r.get("klasse_id")) in klasse_ids
    )
    return FmEditBundle(
        fm_id=target,
        faalwijze_row=copy.deepcopy(faal_row),
        pbs_row=copy.deepcopy(pbs_row),
        fm_effect_rows=tuple(copy.deepcopy(r) for r in fm_effect_rows),
        pm_task_rows=tuple(copy.deepcopy(r) for r in pm_task_rows),
        pm_effect_rows=tuple(copy.deepcopy(r) for r in pm_effect_rows),
        task_group_rows=tuple(copy.deepcopy(r) for r in task_group_rows),
        effect_klasse_rows=tuple(copy.deepcopy(r) for r in effect_klasse_rows),
    )


def load_bundle(project: RCMProject, fm_id: str) -> FmEditBundle:
    target = normalize_key(fm_id)
    fm = project.faalwijzes.get(target)
    if fm is None:
        raise KeyError(f"Onbekende faalwijze: {fm_id}")

    pbs = project.pbs_items.get(fm.pbs_id)
    if pbs is None:
        raise KeyError(f"PBS ontbreekt voor faalwijze {fm_id}: {fm.pbs_id}")

    fm_effect_rows = tuple(
        link.to_dict()
        for link in project.fm_effect_links.values()
        if normalize_key(link.fm_id) == target
    )
    pm_task_rows = tuple(
        task.to_dict()
        for task in project.pm_tasks.values()
        if normalize_key(task.fm_id) == target
    )
    pm_ids = {normalize_key(row["pm_id"]) for row in pm_task_rows}
    pm_effect_rows = tuple(
        link.to_dict()
        for link in project.pm_effect_links.values()
        if normalize_key(link.pm_id) in pm_ids
    )
    group_ids = {
        normalize_key(row.get("task_group_id"))
        for row in pm_task_rows
        if normalize_key(row.get("task_group_id"))
    }
    task_group_rows = tuple(
        group.to_dict()
        for group in project.task_groups.values()
        if normalize_key(group.group_id) in group_ids
    )
    klasse_ids: set[str] = set()
    for row in fm_effect_rows + pm_effect_rows:
        kid = normalize_key(row.get("klasse_id"))
        if kid:
            klasse_ids.add(kid)
    effect_klasse_rows = tuple(
        ek.to_dict()
        for kid, ek in project.effect_klassen.items()
        if normalize_key(kid) in klasse_ids
    )

    return FmEditBundle(
        fm_id=target,
        faalwijze_row=fm.to_dict(),
        pbs_row=pbs.to_dict(),
        fm_effect_rows=fm_effect_rows,
        pm_task_rows=pm_task_rows,
        pm_effect_rows=pm_effect_rows,
        task_group_rows=task_group_rows,
        effect_klasse_rows=effect_klasse_rows,
    )
