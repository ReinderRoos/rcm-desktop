"""Unified workspace presentation cache invalidation graph (slice 37+)."""

from __future__ import annotations

from dataclasses import dataclass, replace

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


@dataclass(frozen=True)
class PresentationInvalidationPlan:
    """Wat na run/state-wijziging opnieuw opgebouwd moet worden."""

    reset_render_index: bool
    startup_disk_modi: frozenset[str]
    lcc_via_render_index: bool


class WorkspacePresentationCache:
    """Eén seam voor presentatie-cache en render-index invalidatie."""

    @staticmethod
    def invalidation_after_run() -> PresentationInvalidationPlan:
        return PresentationInvalidationPlan(
            reset_render_index=True,
            startup_disk_modi=frozenset({MODE_BIJDRAGEN}),
            lcc_via_render_index=True,
        )

    @staticmethod
    def startup_modi() -> frozenset[str]:
        return frozenset({MODE_BIJDRAGEN})

    @staticmethod
    def lcc_uses_render_index() -> bool:
        return True

    @staticmethod
    def default_lcc_warmup_snapshot(snapshot: WorkspaceStateSnapshot) -> WorkspaceStateSnapshot:
        return replace(
            snapshot,
            modus=MODE_LCC,
            scope_id=None,
            lcc_filters=LCCTypeFilterSet.all_on(),
            lcc_calendar_year=None,
            planning_overlay=PlanningOverlayState.inactive(),
        )

    @staticmethod
    def warm_lcc(
        render_index: WorkspaceRenderIndex,
        *,
        project: RCMProject,
        run: RunResult,
        scope_id: str | None,
        cache_modus_key: str,
        overlay: PlanningOverlayState,
        type_filters: LCCTypeFilterSet,
    ) -> object:
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

    @staticmethod
    def disk_rebuild_needed(project: RCMProject, project_path: str, modus: str) -> bool:
        if modus == MODE_LCC and WorkspacePresentationCache.lcc_uses_render_index():
            return False
        return presentation_modus_needs_rebuild(project, project_path, modus)
