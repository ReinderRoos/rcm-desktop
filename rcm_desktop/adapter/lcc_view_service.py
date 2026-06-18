"""Single LCC view entry point (adapter deepening)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rcm_core.models import RCMProject

from rcm_desktop.adapter.lcc_planning_service import LCCPlanningCurve
from rcm_desktop.adapter.lcc_render_cache_service import build_lcc_curve_cache_key, lcc_render_scope
from rcm_desktop.adapter.presentation_lazy_service import warm_lcc_render_index
from rcm_desktop.adapter.results_workspace_state import WorkspaceStateSnapshot
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.workspace_lcc_preset_service import effective_lcc_filters
from rcm_desktop.adapter.workspace_render_index import SLOT_CURRENT, WorkspaceRenderIndex


@dataclass(frozen=True)
class LCCView:
    curve: LCCPlanningCurve | None
    render_scope: Literal["full", "detail_only"]


def build_lcc_view(
    project: RCMProject,
    run: RunResult,
    snapshot: WorkspaceStateSnapshot,
    *,
    render_index: WorkspaceRenderIndex,
    prev_snapshot: WorkspaceStateSnapshot | None,
    slot: str = SLOT_CURRENT,
) -> LCCView:
    """Bouw LCC-curve + render-scope via render-index (één adapter-seam)."""
    scope = lcc_render_scope(prev_snapshot, snapshot)
    cache_modus = build_lcc_curve_cache_key(snapshot)
    curve = warm_lcc_render_index(
        render_index,
        project=project,
        run=run,
        scope_id=snapshot.scope_id,
        cache_modus_key=cache_modus,
        overlay=snapshot.planning_overlay,
        type_filters=effective_lcc_filters(snapshot),
        snapshot=snapshot,
        slot=slot,
    )
    planning_curve = curve if isinstance(curve, LCCPlanningCurve) else None
    return LCCView(curve=planning_curve, render_scope=scope)
