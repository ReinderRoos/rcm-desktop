"""LCC render-cache keys en render-scope (slice 38).

Pure Qt-vrije helpers voor curve vs jaardetail invalidatie.
"""
from __future__ import annotations

from typing import Literal

from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_LCC,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.workspace_lcc_preset_service import effective_lcc_filters

LCCRenderScope = Literal["full", "detail_only"]


def build_lcc_curve_cache_key(snapshot: WorkspaceStateSnapshot) -> str:
    """Cache key voor Tijdsplot-curve — metric, NB-filter, type-filters, overlay."""
    f = effective_lcc_filters(snapshot)
    o = snapshot.planning_overlay
    nb = snapshot.effect_nb_filter
    nb_key = "all" if nb.is_all() else ",".join(sorted(nb.selected_klasse_ids))
    p = snapshot.contribution_presentation
    return (
        f"tijdsplot|{snapshot.metric}|{snapshot.scope_id}|{f.cm}|{f.rev}|{f.in_task}|"
        f"{f.tst}|{f.svo}|{f.wet}|{o.active}|{o.change_count()}|nb:{nb_key}|"
        f"{p.unavailability_display}"
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
    if effective_lcc_filters(previous) != effective_lcc_filters(current):
        return "full"
    if previous.metric != current.metric:
        return "full"
    if previous.effect_nb_filter != current.effect_nb_filter:
        return "full"
    if previous.contribution_presentation.unavailability_display != (
        current.contribution_presentation.unavailability_display
    ):
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
