"""Lazy presentatie-beslissingen — delegeert naar ``WorkspacePresentationCache``."""
from __future__ import annotations

from rcm_core.models import RCMProject

from rcm_desktop.adapter.results_workspace_state import MODE_BIJDRAGEN, MODE_LCC, WorkspaceStateSnapshot
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.workspace_presentation_cache import WorkspacePresentationCache
from rcm_desktop.adapter.workspace_render_index import SLOT_CURRENT, WorkspaceRenderIndex
from rcm_desktop.adapter.lcc_presentatie_service import materialize_lcc_curve


def default_lcc_warmup_snapshot(snapshot: WorkspaceStateSnapshot) -> WorkspaceStateSnapshot:
    return WorkspacePresentationCache.default_lcc_warmup_snapshot(snapshot)


def startup_presentation_modi() -> frozenset[str]:
    return WorkspacePresentationCache.startup_modi()


def lcc_presentation_uses_render_index() -> bool:
    return WorkspacePresentationCache.lcc_uses_render_index()


def warm_lcc_render_index(
    render_index: WorkspaceRenderIndex,
    *,
    project: RCMProject,
    run: RunResult,
    scope_id: str | None,
    cache_modus_key: str,
    overlay,
    type_filters,
    slot: str = SLOT_CURRENT,
) -> object:
    """Lazy LCC warmup — delegeert naar ``materialize_lcc_curve``."""
    return materialize_lcc_curve(
        render_index,
        project=project,
        run=run,
        scope_id=scope_id,
        cache_modus_key=cache_modus_key,
        overlay=overlay,
        type_filters=type_filters,
        slot=slot,
    )


def presentation_rebuild_needed_for_startup(project: RCMProject, project_path: str) -> bool:
    return WorkspacePresentationCache.disk_rebuild_needed(project, project_path, MODE_BIJDRAGEN)


def presentation_rebuild_needed_for_lcc(project: RCMProject, project_path: str) -> bool:
    return WorkspacePresentationCache.disk_rebuild_needed(project, project_path, MODE_LCC)
