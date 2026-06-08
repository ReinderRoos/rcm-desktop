"""Tijdsplot-presentatie — één seam voor LCC-curve + render-index cache."""

from __future__ import annotations

from rcm_core.models import RCMProject

from rcm_desktop.adapter.lcc_planning_service import build_lcc_planning_curve_reconciled
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.run_service import RunResult
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
    slot: str = SLOT_CURRENT,
) -> object:
    """Bouw of haal LCC-curve op uit render-index voor de gevraagde slot."""
    return render_index.get_or_build(
        slot,
        scope_id,
        cache_modus_key,
        lambda: build_lcc_planning_curve_reconciled(
            project,
            run,
            scope_id=scope_id,
            overlay=overlay,
            type_filters=type_filters,
        ),
    )
