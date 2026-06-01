"""Lazy presentatie-beslissingen — delegeert naar ``WorkspacePresentationCache``."""
from __future__ import annotations

from rcm_core.models import RCMProject

from rcm_desktop.adapter.results_workspace_state import MODE_BIJDRAGEN, MODE_LCC, WorkspaceStateSnapshot
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.workspace_presentation_cache import WorkspacePresentationCache
from rcm_desktop.adapter.workspace_render_index import SLOT_CURRENT, WorkspaceRenderIndex
from rcm_desktop.adapter.lcc_planning_service import (
    build_lcc_planning_curve_reconciled as _REAL_BUILD_LCC_PLANNING_CURVE_RECONCILED,
)


def build_lcc_planning_curve_reconciled(
    project: RCMProject,
    run: RunResult,
    *,
    scope_id: str | None,
    overlay,
    type_filters,
    **kwargs,
) -> object:
    """Dispatcher for the LCC planning-curve builder (test-seams).

    - If `rcm_desktop.views.results_workspace_window.build_lcc_planning_curve_reconciled`
      is monkeypatched (test-seam #1), call that patched function.
    - Otherwise fall back to the canonical domain implementation
      (`rcm_desktop.adapter.lcc_planning_service.build_lcc_planning_curve_reconciled`).

    Tests are allowed to monkeypatch *this* symbol as well (test-seam #2),
    replacing the dispatcher entirely.
    """

    try:
        from rcm_desktop.views import results_workspace_window as rww

        view_builder = getattr(rww, "build_lcc_planning_curve_reconciled", None)
        if view_builder is not None and view_builder is not _REAL_BUILD_LCC_PLANNING_CURVE_RECONCILED:
            return view_builder(
                project,
                run,
                scope_id=scope_id,
                overlay=overlay,
                type_filters=type_filters,
                **kwargs,
            )
    except Exception:
        # If the view module is not importable, just fall back.
        pass

    return _REAL_BUILD_LCC_PLANNING_CURVE_RECONCILED(
        project,
        run,
        scope_id=scope_id,
        overlay=overlay,
        type_filters=type_filters,
        **kwargs,
    )


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
) -> object:
    """Lazy LCC warmup via module-level ``build_lcc_planning_curve_reconciled`` (test-seam)."""
    # Test seam: `tests/test_desktop_results_workspace_window.py` monkeypatches
    # `rcm_desktop.views.results_workspace_window.build_lcc_planning_curve_reconciled`.
    # We resolve that symbol at call-time to avoid import-time cycles and so
    # the monkeypatch remains effective.
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


def presentation_rebuild_needed_for_startup(project: RCMProject, project_path: str) -> bool:
    return WorkspacePresentationCache.disk_rebuild_needed(project, project_path, MODE_BIJDRAGEN)


def presentation_rebuild_needed_for_lcc(project: RCMProject, project_path: str) -> bool:
    return WorkspacePresentationCache.disk_rebuild_needed(project, project_path, MODE_LCC)
