"""Qt-vrije PBS-scope-regels voor Input entiteiten-grid (slice 87, ADR-0014)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from rcm_core.models import RCMProject

from rcm_desktop.adapter.result_filter_service import collect_pbs_subtree_ids

_PBS_BOUND_VIEWS = frozenset(
    {
        "input.faalwijzen",
        "input.rev_tasks",
        "input.correctief",
    }
)
_PROJECT_WIDE_VIEWS = frozenset(
    {
        "input.effecten",
        "input.taakgroepen",
    }
)


class InputScopeMode(Enum):
    PBS_BOUND = "pbs_bound"
    PROJECT_WIDE = "project_wide"


def input_scope_mode(view_id: str) -> InputScopeMode:
    if view_id in _PBS_BOUND_VIEWS:
        return InputScopeMode.PBS_BOUND
    if view_id in _PROJECT_WIDE_VIEWS:
        return InputScopeMode.PROJECT_WIDE
    raise ValueError(f"Onbekende Input-grid view_id: {view_id!r}")


def row_pbs_id(view_id: str, row_values: dict[str, Any], project: RCMProject) -> str | None:
    if view_id in ("input.faalwijzen", "input.correctief"):
        raw = row_values.get("pbs_id")
        return str(raw).strip() if raw else None
    if view_id == "input.rev_tasks":
        fm_id = str(row_values.get("fm_id") or "").strip()
        if not fm_id:
            return None
        fw = project.faalwijzes.get(fm_id)
        if fw is None:
            return None
        return fw.pbs_id
    return None


def row_in_scope(
    view_id: str,
    row_values: dict[str, Any],
    project: RCMProject,
    scope_id: str | None,
) -> bool:
    if input_scope_mode(view_id) == InputScopeMode.PROJECT_WIDE:
        return True
    if scope_id is None:
        return True
    if scope_id not in project.pbs_items:
        return False
    pbs_id = row_pbs_id(view_id, row_values, project)
    if not pbs_id:
        return False
    subtree = collect_pbs_subtree_ids(project, scope_id)
    return pbs_id in subtree
