"""Canonieke FM-edit scope loader — project of EditingSession (slice 50)."""

from __future__ import annotations

import copy
from typing import Any

from rcm_core.editing.validation import normalize_key
from rcm_core.models import RCMProject

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.fm_create_service import (
    allocate_fm_id,
    default_faalwijze_row,
    default_functie_id_for_pbs,
)
from rcm_desktop.adapter.fm_edit_bundle_service import FmEditBundle, _edit_current


def load_fm_edit_scope(source: RCMProject | EditingSession, fm_id: str) -> FmEditBundle:
    """Laad ``FmEditBundle`` voor één faalwijze uit project of actieve editsessie."""
    if isinstance(source, EditingSession):
        return _load_from_session(source, fm_id)
    return _load_from_project(source, fm_id)


def seed_create_bundle(session: EditingSession, pbs_id: str) -> FmEditBundle:
    """Lege FM-scope voor create-modus op een leaf-PBS."""
    if not session.is_loaded:
        raise RuntimeError("EditingSession is niet geladen")
    target_pbs = normalize_key(pbs_id)
    current = _edit_current(session)
    pbs_row = next(
        (r for r in current.get("pbs", []) if normalize_key(r.get("pbs_id")) == target_pbs),
        None,
    )
    if pbs_row is None:
        raise KeyError(f"Onbekende PBS in sessie: {pbs_id}")
    fm_id = allocate_fm_id(session)
    functie_id = default_functie_id_for_pbs(session, target_pbs)
    return FmEditBundle(
        fm_id=fm_id,
        faalwijze_row=default_faalwijze_row(
            fm_id=fm_id, pbs_id=target_pbs, functie_id=functie_id
        ),
        pbs_row=copy.deepcopy(pbs_row),
        fm_effect_rows=(),
        pm_effect_rows=(),
        pm_task_rows=(),
        task_group_rows=(),
        effect_klasse_rows=(),
    )


def _load_from_session(session: EditingSession, fm_id: str) -> FmEditBundle:
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


def _load_from_project(project: RCMProject, fm_id: str) -> FmEditBundle:
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
