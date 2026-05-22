"""LCC render-cache keys en render-scope (slice 38).

Pure Qt-vrije helpers voor curve vs jaardetail invalidatie.
"""
from __future__ import annotations

from typing import Literal

from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.results_workspace_state import MODE_LCC, WorkspaceStateSnapshot

LCCRenderScope = Literal["full", "detail_only"]


def build_lcc_curve_cache_key(snapshot: WorkspaceStateSnapshot) -> str:
    """Cache key voor LCC-planningcurve — zonder kalenderjaar."""
    f = snapshot.lcc_filters
    o = snapshot.planning_overlay
    return (
        f"lcc_curve|{snapshot.scope_id}|{f.cm}|{f.rev}|{f.in_task}|{f.tst}|{f.svo}|{f.wet}|"
        f"{o.active}|{o.change_count()}"
    )


def build_lcc_detail_cache_key(snapshot: WorkspaceStateSnapshot) -> str:
    """Detail-identiteit: curve-key + geselecteerd kalenderjaar."""
    year = snapshot.lcc_calendar_year
    return f"{build_lcc_curve_cache_key(snapshot)}|detail|{year}"


def lcc_render_scope(
    previous: WorkspaceStateSnapshot | None,
    current: WorkspaceStateSnapshot,
) -> LCCRenderScope:
    """Bepaal of LCC volledig of alleen jaardetail opnieuw rendert."""
    if previous is None or current.modus != MODE_LCC:
        return "full"
    if previous.modus != MODE_LCC:
        return "full"
    if previous.scope_id != current.scope_id:
        return "full"
    if previous.lcc_filters != current.lcc_filters:
        return "full"
    if previous.planning_overlay != current.planning_overlay:
        return "full"
    if previous.lcc_calendar_year != current.lcc_calendar_year:
        return "detail_only"
    return "full"


def lcc_curve_inputs_changed(
    previous: WorkspaceStateSnapshot | None,
    current: WorkspaceStateSnapshot,
) -> bool:
    """True wanneer curve-cache key zou wijzigen."""
    if previous is None:
        return True
    return build_lcc_curve_cache_key(previous) != build_lcc_curve_cache_key(current)
