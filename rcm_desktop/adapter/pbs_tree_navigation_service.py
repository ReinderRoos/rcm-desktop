"""PBS-boom navigatie-targets (slice 86)."""

from __future__ import annotations

from typing import Literal

from rcm_core.models import RCMProject

from rcm_desktop.adapter.pbs_order_service import sibling_pbs_ids_sorted

NavigationAction = Literal[
    "prev_sibling",
    "next_sibling",
    "parent",
    "first_child",
]


def pbs_id_for_navigation(
    project: RCMProject,
    current_pbs_id: str,
    action: NavigationAction,
) -> str | None:
    item = project.pbs_items.get(current_pbs_id)
    if item is None:
        return None
    parent = item.parent_pbs_id
    if parent is not None and parent not in project.pbs_items:
        parent = None
    siblings = sibling_pbs_ids_sorted(project, parent_pbs_id=parent)
    if action == "parent":
        return parent
    if action == "first_child":
        children = sibling_pbs_ids_sorted(project, parent_pbs_id=current_pbs_id)
        return children[0] if children else None
    if current_pbs_id not in siblings:
        return None
    idx = siblings.index(current_pbs_id)
    if action == "prev_sibling":
        return siblings[idx - 1] if idx > 0 else None
    if action == "next_sibling":
        return siblings[idx + 1] if idx < len(siblings) - 1 else None
    return None
