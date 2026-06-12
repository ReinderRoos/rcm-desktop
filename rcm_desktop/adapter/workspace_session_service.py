"""ProjectSession façade for the resultatenwerkruimte (slice 53 PR1b).

Views pass ``ProjectSession``; kern-toegang blijft in de adapter.
"""

from __future__ import annotations

from rcm_core.models import RCMProject

from rcm_desktop.adapter.analysis_cache_service import (
    fm_cache_available,
    hydrate_run_from_cache,
)
from rcm_desktop.adapter.fm_verification_service import (
    FMVerificationView,
    build_fm_verification_view,
)
from rcm_desktop.adapter.kpi_table_service import KPITable, build_kpi_table
from rcm_desktop.adapter.lcc_planning_service import (
    LCCYearDetailView,
    build_lcc_year_detail,
)
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.planning_cm_preset_service import apply_cm_policy_preset
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_whatif_service import (
    WhatIfActionResult,
    apply_overlay_shift,
)
from rcm_desktop.adapter.presentation_cache_service import (
    PresentationProjectTotal,
    load_presentation_from_cache,
)
from rcm_desktop.adapter.presentation_lazy_service import (
    presentation_rebuild_needed_for_startup,
)
from rcm_desktop.adapter.contribution_horizon_value_service import (
    calendar_years_for_project,
)
from rcm_desktop.adapter.rcm_navigation_tree_builder import build_rcm_navigation_tree
from rcm_desktop.adapter.rcm_navigation_tree_model import RcmNavigationTreeModel
from rcm_desktop.adapter.result_view_service import build_pbs_structure_tree
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.run_service import RunResult


def editing_project(session: ProjectSession) -> RCMProject:
    """Mutatie-/dialoog-pad: FM-editor, batch-grid, Modelinstellingen, run-runner."""
    return session.loaded.core()


def fm_exists(session: ProjectSession, fm_id: str) -> bool:
    return fm_id in session.loaded.core().faalwijzes


def fm_cache_available_for_session(session: ProjectSession, project_path: str) -> bool:
    return fm_cache_available(session.loaded.core(), project_path)


def scope_bouwdeel_naam(session: ProjectSession, pbs_id: str) -> str:
    project = session.loaded.core()
    item = project.pbs_items.get(pbs_id)
    return item.bouwdeel_naam if item is not None else ""


def has_functies(session: ProjectSession) -> bool:
    return bool(session.loaded.core().functies)


def build_navigation_tree_model_for_session(session: ProjectSession) -> RcmNavigationTreeModel:
    project = session.loaded.core()
    return RcmNavigationTreeModel(build_rcm_navigation_tree(project), project)


def build_pbs_structure_tree_for_session(session: ProjectSession):
    return build_pbs_structure_tree(session.loaded.core())


def build_kpi_table_for_session(
    session: ProjectSession | None,
    *,
    run_result: RunResult | None,
    scope_id: str | None,
) -> KPITable:
    project = session.loaded.core() if session is not None else None
    return build_kpi_table(
        project=project,
        run_result=run_result,
        scope_id=scope_id,
    )


def build_fm_verification_for_session(
    session: ProjectSession,
    fmr: object,
    *,
    nb_filter: object | None = None,
) -> FMVerificationView:
    return build_fm_verification_view(session.loaded.core(), fmr, nb_filter=nb_filter)


def build_lcc_year_detail_for_session(
    session: ProjectSession,
    run_result: RunResult,
    calendar_year: int,
    *,
    scope_id: str | None,
    overlay: PlanningOverlayState | None,
    type_filters: LCCTypeFilterSet | None,
    planning_curve=None,
) -> LCCYearDetailView | None:
    return build_lcc_year_detail(
        session.loaded.core(),
        run_result,
        calendar_year,
        scope_id=scope_id,
        overlay=overlay,
        type_filters=type_filters,
        planning_curve=planning_curve,
    )


def overlay_all_rev_passive(session: ProjectSession, overlay: PlanningOverlayState) -> bool:
    return overlay.all_rev_passive(session.loaded.core())


def toggle_bulk_rev_overlay(
    session: ProjectSession,
    overlay: PlanningOverlayState,
) -> PlanningOverlayState:
    project = session.loaded.core()
    if overlay.all_rev_passive(project):
        return overlay.bulk_all_rev_active(project)
    return overlay.bulk_all_rev_passive(project)


def apply_cm_preset_for_session(
    session: ProjectSession,
    overlay: PlanningOverlayState,
) -> PlanningOverlayState:
    return apply_cm_policy_preset(overlay, session.loaded.core())


def apply_overlay_shift_for_session(
    session: ProjectSession,
    overlay: PlanningOverlayState,
    *,
    pm_ids: list[str],
    shift_years: int,
) -> WhatIfActionResult:
    return apply_overlay_shift(
        session.loaded.core(),
        overlay,
        pm_ids=pm_ids,
        shift_years=shift_years,
    )


def load_presentation_for_session(
    session: ProjectSession,
    project_path: str,
) -> PresentationProjectTotal | None:
    return load_presentation_from_cache(session.loaded.core(), project_path)


def presentation_rebuild_needed_for_session(
    session: ProjectSession,
    project_path: str,
) -> bool:
    return presentation_rebuild_needed_for_startup(session.loaded.core(), project_path)


def hydrate_run_for_session(
    session: ProjectSession,
    project_path: str,
) -> RunResult | None:
    return hydrate_run_from_cache(session.loaded.core(), project_path)


def calendar_years_for_session(session: ProjectSession) -> tuple[int, ...]:
    return calendar_years_for_project(session.loaded.core())
