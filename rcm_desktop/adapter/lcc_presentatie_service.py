"""Tijdsplot-presentatie — één seam voor metric-gedreven curve + render-index cache."""

from __future__ import annotations

from dataclasses import replace

from rcm_core.models import RCMProject

from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.results_workspace_state import WorkspaceStateSnapshot
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.tijdsplot_curve_service import build_tijdsplot_curve
from rcm_desktop.adapter.workspace_render_index import SLOT_CURRENT, WorkspaceRenderIndex


def materialize_lcc_curve(
    render_index: WorkspaceRenderIndex,
    *,
    project: RCMProject,
    run: RunResult,
    scope_id: str | None,
    cache_modus_key: str,
    overlay: PlanningOverlayState,
    type_filters: LCCTypeFilterSet,
    snapshot: WorkspaceStateSnapshot,
    slot: str = SLOT_CURRENT,
) -> object:
    """Bouw of haal Tijdsplot-curve op uit render-index voor de gevraagde slot."""
    snap = replace(snapshot, scope_id=scope_id) if scope_id != snapshot.scope_id else snapshot
    return render_index.get_or_build(
        slot,
        scope_id,
        cache_modus_key,
        lambda: build_tijdsplot_curve(project, run, snap, scope_id=scope_id),
    )
