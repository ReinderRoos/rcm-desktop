"""Qt-vrije derived workspace state voor presentatie-refresh (slice 92)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from rcm_core.models import FMResult, RCMProject

from rcm_desktop.adapter.contribution_horizon_value_service import (
    calendar_years_for_project,
)
from rcm_desktop.adapter.kpi_table_service import KPITable
from rcm_desktop.adapter.nb_effect_filter_presentation import (
    NbEffectFilterPresentation,
    build_nb_effect_filter_presentation,
)
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.result_view_service import PBSTreeNode
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.workspace_session_service import (
    build_kpi_table_for_session,
    build_pbs_structure_tree_for_session,
    has_functies,
)

PbsTreeKind = Literal["empty", "run_results", "navigation", "structure"]


@dataclass(frozen=True)
class PbsTreeRefreshPlan:
    kind: PbsTreeKind
    roots: tuple[PBSTreeNode, ...] = ()
    show_totals: bool = False


def plan_nb_filter_refresh(
    project: RCMProject | None,
    fm_results: Sequence[FMResult] = (),
) -> NbEffectFilterPresentation:
    """Bereken NbEffectFilterPresentation uit project en run-resultaten.

    Pure functie — geen Qt vereist. Geeft een lege presentatie terug als
    ``project`` None is; anders delegeert naar ``build_nb_effect_filter_presentation``.
    """
    if project is None:
        return NbEffectFilterPresentation(entries=())
    return build_nb_effect_filter_presentation(project, fm_results)


def plan_contribution_year_refresh(project: RCMProject | None) -> tuple[int, ...]:
    """Bereken kalenderjaren voor de bijdragen-jaarkiezer uit een project.

    Pure functie — geen Qt vereist. Lege tuple als ``project`` None is.
    """
    if project is None:
        return ()
    return calendar_years_for_project(project)


def plan_kpi_refresh(
    session: ProjectSession | None,
    *,
    run_result: RunResult | None,
    scope_id: str | None,
) -> KPITable:
    """Bereken KPI-tabel voor de werkruimte (slice 95)."""
    return build_kpi_table_for_session(session, run_result=run_result, scope_id=scope_id)


def plan_pbs_tree_refresh(
    session: ProjectSession | None,
    *,
    run_result: RunResult | None,
) -> PbsTreeRefreshPlan:
    """Bereken PBS-boomplan voor sync (slice 95)."""
    if session is None:
        return PbsTreeRefreshPlan(kind="empty")
    if (
        isinstance(run_result, RunResult)
        and run_result.status == "done"
        and run_result.pbs_rows
    ):
        from rcm_desktop.adapter.result_view_service import build_pbs_tree

        roots = build_pbs_tree(list(run_result.pbs_rows))
        return PbsTreeRefreshPlan(kind="run_results", roots=roots, show_totals=True)
    if has_functies(session):
        return PbsTreeRefreshPlan(kind="navigation", show_totals=False)
    roots = build_pbs_structure_tree_for_session(session)
    return PbsTreeRefreshPlan(kind="structure", roots=roots, show_totals=False)
