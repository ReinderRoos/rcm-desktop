"""Lazy presentatie-beslissingen (slice 37).

LCC-presentatie leeft in `WorkspaceRenderIndex` + LTAP-cache (slice 36),
niet in `.rcm.cache.json` presentation-blok.
"""
from __future__ import annotations

from dataclasses import replace

from rcm_core.models import RCMProject

from rcm_desktop.adapter.lcc_planning_service import build_lcc_planning_curve_reconciled
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.presentation_cache_service import presentation_modus_needs_rebuild
from rcm_desktop.adapter.results_workspace_state import (
    MODE_BIJDRAGEN,
    MODE_LCC,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.workspace_render_index import SLOT_CURRENT, WorkspaceRenderIndex


def default_lcc_warmup_snapshot(snapshot: WorkspaceStateSnapshot) -> WorkspaceStateSnapshot:
    """Default LCC-curve voor achtergrond-warmup na run (slice 38)."""
    return replace(
        snapshot,
        modus=MODE_LCC,
        scope_id=None,
        lcc_filters=LCCTypeFilterSet.all_on(),
        lcc_calendar_year=None,
        planning_overlay=PlanningOverlayState.inactive(),
    )


def startup_presentation_modi() -> frozenset[str]:
    """Modi die direct na run/rebuild in presentatie-cache worden gebouwd."""
    return frozenset({MODE_BIJDRAGEN})


def lcc_presentation_uses_render_index() -> bool:
    """LCC wordt niet via presentatie-cache worker gebouwd (slice 37)."""
    return True


def warm_lcc_render_index(
    render_index: WorkspaceRenderIndex,
    *,
    project: RCMProject,
    run: RunResult,
    scope_id: str | None,
    cache_modus_key: str,
    overlay,
    type_filters,
) -> object:
    """Lazy LCC warmup: eerste modusbezoek bouwt curve in render_index."""
    return render_index.get_or_build(
        SLOT_CURRENT,
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


def presentation_rebuild_needed_for_startup(
    project: RCMProject,
    project_path: str,
) -> bool:
    """True wanneer contribution-blok ontbreekt (niet voor LCC)."""
    return presentation_modus_needs_rebuild(project, project_path, MODE_BIJDRAGEN)


def presentation_rebuild_needed_for_lcc(
    project: RCMProject,
    project_path: str,
) -> bool:
    """LCC vereist geen presentatie-cache rebuild."""
    return presentation_modus_needs_rebuild(project, project_path, MODE_LCC)
