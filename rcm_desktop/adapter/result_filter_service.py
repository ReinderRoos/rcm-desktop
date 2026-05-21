"""Qt-vrije presentatie-adapter: filter een `RunResult` op PBS-scope.

Scope-filter werkt op de **presentatielaag**: er wordt geen motor aangeroepen.
`scope_id=None` betekent "hele project"; een onbekende `scope_id` levert een
lege view op (geen impliciete fallback naar projectbreed).
"""
from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import FMResult, RCMProject
from rcm_desktop.adapter.result_view_service import (
    FMResultRow,
    PBSResultRow,
    PBSTreeNode,
    build_pbs_tree,
)
from rcm_desktop.adapter.run_service import RunResult


@dataclass(frozen=True)
class ScopedKPITotals:
    """Vier kerngetallen voor één scope: faalmomenten, downtime, kosten, niet-beschikbaarheid %."""

    total_faalmomenten: float
    total_downtime_hr: float
    total_cost_eur: float
    unavailability_pct: float


@dataclass(frozen=True)
class FilteredRunView:
    """Resultaat van een scope-filter; alleen presentatie, geen motor-state."""

    scope_id: str | None
    fm_rows: tuple[FMResultRow, ...]
    pbs_rows: tuple[PBSResultRow, ...]
    pbs_tree_roots: tuple[PBSTreeNode, ...]
    kpi_totals: ScopedKPITotals


def filter_run_result(
    project: RCMProject,
    run_result: RunResult,
    scope_id: str | None,
) -> FilteredRunView:
    """Filter een `RunResult` op een PBS-scope.

    - `scope_id=None`: hele project (alle rijen, totalen reconciliëren met motor).
    - `scope_id` aanwezig in `project.pbs_items`: filter op subtree (zelf + descendants).
    - `scope_id` onbekend: lege view met nul-totalen.
    """
    lifecycle_years = float(project.config.lifecycle_years)
    lifecycle_hours = lifecycle_years * 8760.0

    if scope_id is None:
        kpi = _aggregate_kpi(run_result.fm_core_results, lifecycle_hours)
        return FilteredRunView(
            scope_id=None,
            fm_rows=tuple(run_result.rows),
            pbs_rows=tuple(run_result.pbs_rows),
            pbs_tree_roots=build_pbs_tree(list(run_result.pbs_rows)),
            kpi_totals=kpi,
        )

    if scope_id not in project.pbs_items:
        return FilteredRunView(
            scope_id=scope_id,
            fm_rows=(),
            pbs_rows=(),
            pbs_tree_roots=(),
            kpi_totals=ScopedKPITotals(
                total_faalmomenten=0.0,
                total_downtime_hr=0.0,
                total_cost_eur=0.0,
                unavailability_pct=0.0,
            ),
        )

    subtree_ids = _collect_subtree_ids(project, scope_id)
    fm_rows = tuple(row for row in run_result.rows if row.pbs_id in subtree_ids)
    pbs_rows = tuple(row for row in run_result.pbs_rows if row.pbs_id in subtree_ids)
    fm_core = tuple(fmr for fmr in run_result.fm_core_results if fmr.pbs_id in subtree_ids)
    kpi = _aggregate_kpi(fm_core, lifecycle_hours)
    tree_roots = _build_subtree_roots(pbs_rows, scope_id)
    return FilteredRunView(
        scope_id=scope_id,
        fm_rows=fm_rows,
        pbs_rows=pbs_rows,
        pbs_tree_roots=tree_roots,
        kpi_totals=kpi,
    )


def _aggregate_kpi(
    fm_results: "tuple[FMResult, ...] | list[FMResult]", lifecycle_hours: float
) -> ScopedKPITotals:
    """Aggregeer KPI's uit motor-`FMResult` (inclusief PM-downtime)."""
    total_failures = 0.0
    total_downtime = 0.0
    total_cost = 0.0
    for fmr in fm_results:
        total_failures += fmr.expected_failures
        total_downtime += fmr.expected_total_downtime_hr + fmr.expected_pm_downtime_hr
        total_cost += fmr.total_cost_eur
    unavailability_pct = (
        0.0 if lifecycle_hours <= 0.0 else (total_downtime / lifecycle_hours) * 100.0
    )
    return ScopedKPITotals(
        total_faalmomenten=total_failures,
        total_downtime_hr=total_downtime,
        total_cost_eur=total_cost,
        unavailability_pct=unavailability_pct,
    )


def collect_pbs_subtree_ids(project: RCMProject, scope_id: str) -> frozenset[str]:
    """PBS-id's in subtree (zelf + descendants)."""
    return _collect_subtree_ids(project, scope_id)


def _collect_subtree_ids(project: RCMProject, scope_id: str) -> frozenset[str]:
    children: dict[str, list[str]] = {}
    for pid, item in project.pbs_items.items():
        if item.parent_pbs_id is None:
            continue
        if item.parent_pbs_id not in project.pbs_items:
            continue
        children.setdefault(item.parent_pbs_id, []).append(pid)

    collected: set[str] = set()
    stack: list[str] = [scope_id]
    while stack:
        current = stack.pop()
        if current in collected:
            continue
        collected.add(current)
        for child_id in children.get(current, ()):
            if child_id not in collected:
                stack.append(child_id)
    return frozenset(collected)


def _build_subtree_roots(
    pbs_rows: tuple[PBSResultRow, ...], scope_id: str
) -> tuple[PBSTreeNode, ...]:
    """Bouw subtree-roots uit gefilterde rijen, met `scope_id` als geforceerde root."""
    if not pbs_rows:
        return ()
    rerooted: list[PBSResultRow] = []
    for row in pbs_rows:
        if row.pbs_id == scope_id:
            rerooted.append(
                PBSResultRow(
                    pbs_id=row.pbs_id,
                    bouwdeel_naam=row.bouwdeel_naam,
                    parent_pbs_id=None,
                    level=0,
                    sort_path=(row.pbs_id,),
                    expected_failures_self=row.expected_failures_self,
                    total_downtime_hr_self=row.total_downtime_hr_self,
                    total_cost_eur_self=row.total_cost_eur_self,
                    expected_failures_total=row.expected_failures_total,
                    total_downtime_hr_total=row.total_downtime_hr_total,
                    total_cost_eur_total=row.total_cost_eur_total,
                    unavailability_pct_total=row.unavailability_pct_total,
                )
            )
        else:
            rerooted.append(row)
    return build_pbs_tree(rerooted)
