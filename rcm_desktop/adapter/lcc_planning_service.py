"""LCC-planning: type-filters, overlay en jaardetail (slice 28)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from rcm_core.lcc_profile import build_cm_eur_per_bucket, ltap_horizon_bucket_count
from rcm_core.models import RCMProject, TaskType

from rcm_desktop.adapter.calendar_year import calendar_year_for_horizon_index
from rcm_desktop.adapter.lcc_chart_service import LCCScenarioCurve, LCCYearBucket, sum_correctief_preventief
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.ltap_service import LTAPTaskDetail, LTAPView
from rcm_desktop.adapter.ltap_view_cache import get_ltap_view
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.result_filter_service import collect_pbs_subtree_ids
from rcm_desktop.adapter.run_service import RunResult


@dataclass(frozen=True)
class LCCPlanningCurve:
    """Baseline + optionele gefilterde presentatie."""

    baseline_buckets: tuple[LCCYearBucket, ...]
    display_buckets: tuple[LCCYearBucket, ...]
    preventief_by_type_per_year: tuple[dict[str, float], ...]


@dataclass(frozen=True)
class LCCYearDetailRow:
    pm_id: str
    pm_label: str
    taak_type: str
    fm_display: str
    executions: int
    pm_cost_eur: float
    planned_downtime_hr: float
    shiftable: bool
    is_passive: bool = False


@dataclass(frozen=True)
class LCCYearDetailView:
    calendar_year: int
    horizon_index: int
    baseline_correctief_eur: float
    baseline_preventief_eur: float
    overlay_correctief_eur: float | None
    overlay_preventief_eur: float | None
    cm_only: bool
    rows: tuple[LCCYearDetailRow, ...]


def _overlay_affects_preventief_presentatie(overlay: PlanningOverlayState) -> bool:
    if not overlay.active:
        return False
    if overlay.disabled_pm_ids:
        return True
    return any(abs(year) > 1e-12 for _, year in overlay.anchor_years)


def _fm_pbs_scope(project: RCMProject, scope_id: str | None) -> frozenset[str] | None:
    if scope_id is None:
        return None
    if scope_id not in project.pbs_items:
        return frozenset()
    return collect_pbs_subtree_ids(project, scope_id)


def _scale_cm_buckets(
    cm: list[float],
    *,
    project: RCMProject,
    run: RunResult,
    fm_pbs_ids: frozenset[str] | None,
) -> list[float]:
    if fm_pbs_ids is None:
        return cm
    if not fm_pbs_ids:
        return [0.0] * len(cm)
    target = sum(
        float(r.expected_cm_cost_eur)
        for r in run.fm_core_results
        if r.pbs_id in fm_pbs_ids
    )
    total = sum(float(r.expected_cm_cost_eur) for r in run.fm_core_results)
    if total <= 1e-15:
        return [0.0] * len(cm)
    factor = target / total
    return [v * factor for v in cm]


def _ltap_preventief_series(
    project: RCMProject,
    *,
    overlay: PlanningOverlayState,
    fm_pbs_ids: frozenset[str] | None,
    disabled_pm_ids: frozenset[str],
    type_filters: LCCTypeFilterSet,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """(on-gefilterde PM per jaar, filter-unie PM per jaar)."""
    view = get_ltap_view(
        project,
        overlay_anchor_years=overlay.anchor_years_dict() if overlay.active else None,
        disabled_pm_ids=disabled_pm_ids,
        fm_pbs_ids=fm_pbs_ids,
    )
    n = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    raw = [0.0] * n
    filtered = [0.0] * n
    for row in view.years:
        if not (0 <= row.year < n):
            continue
        raw[row.year] = float(row.pm_cost_eur)
        seen: set[str] = set()
        part = 0.0
        for detail in row.details:
            if detail.pm_id in seen:
                continue
            task = project.pm_tasks.get(detail.pm_id)
            if task is None or not type_filters.task_matches(task):
                continue
            seen.add(detail.pm_id)
            part += float(detail.pm_cost_eur)
        filtered[row.year] = part
    return tuple(raw), tuple(filtered)


def _buckets_from_parts(
    *,
    project: RCMProject,
    cm: list[float],
    unfiltered_preventief: tuple[float, ...],
) -> tuple[LCCYearBucket, ...]:
    mj = int(project.config.modeljaar)
    built: list[LCCYearBucket] = []
    for h, prev in enumerate(unfiltered_preventief):
        built.append(
            LCCYearBucket(
                calendar_year=calendar_year_for_horizon_index(mj, h),
                correctief_eur=cm[h] if h < len(cm) else 0.0,
                preventief_eur=prev,
            )
        )
    return tuple(built)


def build_lcc_planning_curve(
    project: RCMProject,
    run: RunResult,
    *,
    scope_id: str | None = None,
    overlay: PlanningOverlayState | None = None,
    type_filters: LCCTypeFilterSet | None = None,
) -> LCCPlanningCurve | None:
    if run.status != "done" or not run.fm_core_results:
        return None
    overlay_state = overlay or PlanningOverlayState.inactive()
    filters = type_filters or LCCTypeFilterSet.all_on()
    fm_scope = _fm_pbs_scope(project, scope_id)

    cm_raw = build_cm_eur_per_bucket(project, run.fm_core_results)
    n = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    if len(cm_raw) < n:
        cm_raw = cm_raw + [0.0] * (n - len(cm_raw))
    cm_raw = cm_raw[:n]
    cm_scaled = _scale_cm_buckets(cm_raw, project=project, run=run, fm_pbs_ids=fm_scope)

    inactive = PlanningOverlayState.inactive()
    raw_base, filt_base = _ltap_preventief_series(
        project,
        overlay=inactive,
        fm_pbs_ids=fm_scope,
        disabled_pm_ids=frozenset(),
        type_filters=filters,
    )
    baseline_buckets = _buckets_from_parts(
        project=project, cm=cm_scaled, unfiltered_preventief=raw_base
    )

    raw_overlay, filt_overlay = _ltap_preventief_series(
        project,
        overlay=overlay_state,
        fm_pbs_ids=fm_scope,
        disabled_pm_ids=overlay_state.disabled_pm_ids if overlay_state.active else frozenset(),
        type_filters=filters,
    )
    overlay_buckets = _buckets_from_parts(
        project=project, cm=cm_scaled, unfiltered_preventief=raw_overlay
    )

    target_pm = sum(float(r.pm_cost_eur) for r in run.fm_core_results)
    if fm_scope is not None and fm_scope:
        target_pm = sum(
            float(r.pm_cost_eur) for r in run.fm_core_results if r.pbs_id in fm_scope
        )
    elif fm_scope is not None:
        target_pm = 0.0

    baseline_scaled = reconcile_planning_curve_pm_total(
        LCCPlanningCurve(
            baseline_buckets=baseline_buckets,
            display_buckets=baseline_buckets,
            preventief_by_type_per_year=(),
        ),
        target_pm,
    ).baseline_buckets

    overlay_affects_pm = _overlay_affects_preventief_presentatie(overlay_state)
    if overlay_affects_pm:
        display_buckets = filters.apply_curve(
            overlay_buckets,
            unfiltered_preventief=raw_overlay,
            filtered_preventief=filt_overlay,
        )
    else:
        scaled_prev = tuple(b.preventief_eur for b in baseline_scaled)
        display_buckets = filters.apply_curve(
            baseline_scaled,
            unfiltered_preventief=scaled_prev,
            filtered_preventief=scaled_prev,
        )

    return LCCPlanningCurve(
        baseline_buckets=baseline_scaled,
        display_buckets=display_buckets,
        preventief_by_type_per_year=(),
    )


def reconcile_planning_curve_pm_total(curve: LCCPlanningCurve, target_pm: float) -> LCCPlanningCurve:
    """Schaal preventief zodat som gelijk is aan scoped motor-PM-totaal."""

    def _scale(buckets: tuple[LCCYearBucket, ...]) -> tuple[LCCYearBucket, ...]:
        pm_sum = sum(b.preventief_eur for b in buckets)
        if pm_sum <= 1e-15 or math.isclose(pm_sum, target_pm, rel_tol=0, abs_tol=1e-4):
            return buckets
        factor = target_pm / pm_sum
        return tuple(
            LCCYearBucket(
                calendar_year=b.calendar_year,
                correctief_eur=b.correctief_eur,
                preventief_eur=b.preventief_eur * factor,
            )
            for b in buckets
        )

    return LCCPlanningCurve(
        baseline_buckets=_scale(curve.baseline_buckets),
        display_buckets=_scale(curve.display_buckets),
        preventief_by_type_per_year=curve.preventief_by_type_per_year,
    )


def build_lcc_planning_curve_reconciled(
    project: RCMProject,
    run: RunResult,
    **kwargs,
) -> LCCPlanningCurve | None:
    curve = build_lcc_planning_curve(project, run, **kwargs)
    if curve is None:
        return None
    fm_scope = _fm_pbs_scope(project, kwargs.get("scope_id"))
    target_pm = sum(float(r.pm_cost_eur) for r in run.fm_core_results)
    if fm_scope is not None and fm_scope:
        target_pm = sum(float(r.pm_cost_eur) for r in run.fm_core_results if r.pbs_id in fm_scope)
    elif fm_scope is not None:
        target_pm = 0.0
    reconciled = reconcile_planning_curve_pm_total(
        LCCPlanningCurve(
            baseline_buckets=curve.baseline_buckets,
            display_buckets=curve.baseline_buckets,
            preventief_by_type_per_year=(),
        ),
        target_pm,
    )
    return LCCPlanningCurve(
        baseline_buckets=reconciled.baseline_buckets,
        display_buckets=curve.display_buckets,
        preventief_by_type_per_year=(),
    )


def horizon_index_for_calendar_year(project: RCMProject, calendar_year: int) -> int | None:
    mj = int(project.config.modeljaar)
    idx = calendar_year - mj
    n = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    if 0 <= idx < n:
        return idx
    return None


def build_lcc_year_detail(
    project: RCMProject,
    run: RunResult,
    calendar_year: int,
    *,
    scope_id: str | None = None,
    overlay: PlanningOverlayState | None = None,
    type_filters: LCCTypeFilterSet | None = None,
    planning_curve: LCCPlanningCurve | None = None,
) -> LCCYearDetailView | None:
    if run.status != "done" or not run.fm_core_results:
        return None
    h = horizon_index_for_calendar_year(project, calendar_year)
    if h is None:
        return None
    overlay_state = overlay or PlanningOverlayState.inactive()
    filters = type_filters or LCCTypeFilterSet.all_on()
    fm_scope = _fm_pbs_scope(project, scope_id)
    curve = planning_curve
    if curve is None:
        curve = build_lcc_planning_curve_reconciled(
            project, run, scope_id=scope_id, overlay=overlay_state, type_filters=filters
        )
    if curve is None:
        return None
    base_b = curve.baseline_buckets[h]
    disp_b = curve.display_buckets[h]
    cm_only = filters.cm and not any(
        (filters.rev, filters.in_task, filters.tst, filters.svo, filters.wet)
    )

    rows: list[LCCYearDetailRow] = []
    if not cm_only:
        view = get_ltap_view(
            project,
            overlay_anchor_years=overlay_state.anchor_years_dict() if overlay_state.active else None,
            disabled_pm_ids=overlay_state.disabled_pm_ids if overlay_state.active else frozenset(),
            fm_pbs_ids=fm_scope,
        )
        if h < len(view.years):
            for detail in view.years[h].details:
                task = project.pm_tasks.get(detail.pm_id)
                if task is None or not filters.task_matches(task):
                    continue
                rows.append(
                    _detail_to_row(
                        detail,
                        is_passive=overlay_state.active
                        and detail.pm_id in overlay_state.disabled_pm_ids,
                    )
                )

    return LCCYearDetailView(
        calendar_year=calendar_year,
        horizon_index=h,
        baseline_correctief_eur=base_b.correctief_eur,
        baseline_preventief_eur=base_b.preventief_eur,
        overlay_correctief_eur=disp_b.correctief_eur if overlay_state.active else None,
        overlay_preventief_eur=disp_b.preventief_eur if overlay_state.active else None,
        cm_only=cm_only,
        rows=tuple(rows),
    )


def _detail_to_row(detail: LTAPTaskDetail, *, is_passive: bool = False) -> LCCYearDetailRow:
    return LCCYearDetailRow(
        pm_id=detail.pm_id,
        pm_label=detail.pm_label,
        taak_type=detail.taak_type,
        fm_display=detail.fm_display,
        executions=detail.executions,
        pm_cost_eur=detail.pm_cost_eur,
        planned_downtime_hr=detail.planned_downtime_hr,
        shiftable=detail.shiftable,
        is_passive=is_passive,
    )


def planning_curve_as_scenario(curve: LCCPlanningCurve, *, label: str) -> LCCScenarioCurve:
    return LCCScenarioCurve(scenario_key="PLANNING", label=label, buckets=curve.display_buckets)
