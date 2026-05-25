"""Laadt één FM-scope voor de faalwijze-editor (Qt-vrij)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rcm_core.editing.validation import normalize_key
from rcm_core.models import RCMProject


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


def count_faalwijzen_for_pbs(project: RCMProject, pbs_id: str) -> int:
    target = normalize_key(pbs_id)
    return sum(1 for fm in project.faalwijzes.values() if normalize_key(fm.pbs_id) == target)


def count_faalwijzen_for_task_group(project: RCMProject, group_id: str) -> int:
    target = normalize_key(group_id)
    if not target:
        return 0
    pm_ids = {
        normalize_key(pm.pm_id)
        for pm in project.pm_tasks.values()
        if normalize_key(pm.task_group_id) == target
    }
    fm_ids = {
        normalize_key(project.pm_tasks[pid].fm_id)
        for pid in pm_ids
        if pid in project.pm_tasks
    }
    return len(fm_ids)


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
