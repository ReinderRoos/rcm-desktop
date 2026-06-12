"""PBS sibling-volgorde: sorteren en swap (slice 86)."""

from __future__ import annotations

from dataclasses import replace
from typing import Literal

from rcm_core.models import PBSItem, RCMProject

ReorderDirection = Literal["up", "down"]


def _parent_key(item: PBSItem, project: RCMProject) -> str | None:
    parent = item.parent_pbs_id
    if parent is None or parent not in project.pbs_items:
        return None
    return parent


def sibling_pbs_ids_sorted(
    project: RCMProject,
    *,
    parent_pbs_id: str | None,
) -> tuple[str, ...]:
    siblings = [
        pid
        for pid, item in project.pbs_items.items()
        if _parent_key(item, project) == parent_pbs_id
    ]
    siblings.sort(key=lambda pid: (project.pbs_items[pid].volgorde, pid))
    return tuple(siblings)


def swap_pbs_sibling_order(
    project: RCMProject,
    pbs_id: str,
    *,
    direction: ReorderDirection,
) -> tuple[RCMProject, bool]:
    """Wissel ``volgorde`` met de directe buur; geen parent-wijziging."""
    item = project.pbs_items.get(pbs_id)
    if item is None:
        return project, False
    parent = _parent_key(item, project)
    siblings = list(sibling_pbs_ids_sorted(project, parent_pbs_id=parent))
    if pbs_id not in siblings:
        return project, False
    idx = siblings.index(pbs_id)
    if direction == "up":
        if idx == 0:
            return project, False
        neighbor = siblings[idx - 1]
    else:
        if idx >= len(siblings) - 1:
            return project, False
        neighbor = siblings[idx + 1]
    a = project.pbs_items[pbs_id]
    b = project.pbs_items[neighbor]
    new_items = dict(project.pbs_items)
    new_items[pbs_id] = replace(a, volgorde=b.volgorde)
    new_items[neighbor] = replace(b, volgorde=a.volgorde)
    return replace(project, pbs_items=new_items), True
