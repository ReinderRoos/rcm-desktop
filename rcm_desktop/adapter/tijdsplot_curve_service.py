"""Metric-gedreven Tijdsplot-curve (slice 71 issue 05)."""

from __future__ import annotations

import math

from rcm_core.effect_impact_service import EffectNbFilterSet, EffectPresentation, nb_yearly_series
from rcm_core.lcc_profile import ltap_horizon_bucket_count
from rcm_core.models import RCMProject

from rcm_desktop.adapter.calendar_year import calendar_year_for_horizon_index
from rcm_desktop.adapter.horizon_bucket_series import faalmomenten_per_bucket
from rcm_desktop.adapter.lcc_chart_service import LCCYearBucket
from rcm_desktop.adapter.lcc_planning_service import (
    LCCPlanningCurve,
    build_lcc_planning_curve_reconciled,
)
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.result_filter_service import collect_pbs_subtree_ids
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    ContributionPresentation,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.workspace_lcc_preset_service import effective_lcc_filters


def build_tijdsplot_curve(
    project: RCMProject,
    run: RunResult,
    snapshot: WorkspaceStateSnapshot,
    *,
    scope_id: str | None = None,
) -> LCCPlanningCurve | None:
    """Bouw Tijdsplot-curve volgens gedeelde workspace metric."""
    metric = snapshot.metric
    if metric == METRIC_KOSTEN:
        return build_lcc_planning_curve_reconciled(
            project,
            run,
            scope_id=scope_id,
            overlay=snapshot.planning_overlay,
            type_filters=effective_lcc_filters(snapshot),
        )
    if metric == METRIC_NIET_BESCHIKBAARHEID:
        return _build_nb_curve(project, run, snapshot, scope_id=scope_id)
    if metric == METRIC_FAALMOMENTEN:
        return _build_faalmomenten_curve(project, run, scope_id=scope_id)
    return None


def _scoped_fm_results(
    project: RCMProject,
    run: RunResult,
    scope_id: str | None,
) -> tuple:
    fm_results = run.fm_core_results
    if scope_id is None:
        return fm_results
    if scope_id not in project.pbs_items:
        return ()
    subtree = collect_pbs_subtree_ids(project, scope_id)
    return tuple(fmr for fmr in fm_results if fmr.pbs_id in subtree)


def _build_nb_curve(
    project: RCMProject,
    run: RunResult,
    snapshot: WorkspaceStateSnapshot,
    *,
    scope_id: str | None,
) -> LCCPlanningCurve | None:
    if run.status != "done" or not run.fm_core_results:
        return None
    pres = snapshot.contribution_presentation
    effect_pres = EffectPresentation(
        horizon="per_year",
        unavailability_display=pres.unavailability_display,
    )
    fm_dict = {fr.fm_id: fr for fr in run.fm_core_results}
    series = nb_yearly_series(
        project,
        fm_dict,
        nb_filter=snapshot.effect_nb_filter,
        scope_id=scope_id,
        presentation=effect_pres,
    )
    n = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    if len(series) < n:
        series = list(series) + [0.0] * (n - len(series))
    series = series[:n]
    mj = int(project.config.modeljaar)
    buckets: list[LCCYearBucket] = []
    for h in range(n):
        cy = calendar_year_for_horizon_index(mj, h)
        val = float(series[h])
        buckets.append(LCCYearBucket(calendar_year=cy, correctief_eur=val, preventief_eur=0.0))
    tup = tuple(buckets)
    return LCCPlanningCurve(
        baseline_buckets=tup,
        display_buckets=tup,
        preventief_by_type_per_year=tuple({} for _ in range(n)),
    )


def _build_faalmomenten_curve(
    project: RCMProject,
    run: RunResult,
    *,
    scope_id: str | None,
) -> LCCPlanningCurve | None:
    scoped = _scoped_fm_results(project, run, scope_id)
    if not scoped:
        return None
    n = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    totals = [0.0] * n
    for fmr in scoped:
        buckets = faalmomenten_per_bucket(project, fmr)
        while len(buckets) < n:
            buckets = buckets + [0.0]
        for h in range(n):
            totals[h] += float(buckets[h])
    target = sum(float(fmr.expected_failures) for fmr in scoped)
    got = sum(totals)
    if got > 0 and not math.isclose(got, target, rel_tol=0, abs_tol=1e-4):
        scale = target / got
        totals = [v * scale for v in totals]
    mj = int(project.config.modeljaar)
    built = tuple(
        LCCYearBucket(
            calendar_year=calendar_year_for_horizon_index(mj, h),
            correctief_eur=totals[h],
            preventief_eur=0.0,
        )
        for h in range(n)
    )
    return LCCPlanningCurve(
        baseline_buckets=built,
        display_buckets=built,
        preventief_by_type_per_year=tuple({} for _ in range(n)),
    )
