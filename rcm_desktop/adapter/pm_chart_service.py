"""PM jaargrafiek-input (presentatie, Qt-vrij)."""
from __future__ import annotations

from dataclasses import dataclass

from rcm_core.lcc_profile import ltap_horizon_bucket_count
from rcm_core.models import RCMProject

from rcm_desktop.adapter.calendar_year import calendar_year_for_horizon_index
from rcm_desktop.adapter.lcc_planning_service import build_lcc_planning_curve_reconciled
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.ltap_service import build_ltap_view
from rcm_desktop.adapter.ltap_view_cache import get_ltap_view
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.result_filter_service import collect_pbs_subtree_ids
from rcm_desktop.adapter.run_service import RunResult

PM_SUBMODE_KOSTEN = "kosten"
PM_SUBMODE_AANTAL_UITVOERINGEN = "aantal_uitvoeringen"
ALL_PM_SUBMODES: tuple[str, ...] = (
    PM_SUBMODE_KOSTEN,
    PM_SUBMODE_AANTAL_UITVOERINGEN,
)


@dataclass(frozen=True)
class PMYearRow:
    calendar_year: int
    value: float
    cumulative: float


@dataclass(frozen=True)
class PMChartInput:
    submode: str
    scope_id: str | None
    rows: tuple[PMYearRow, ...]


def build_pm_chart_input(
    project: RCMProject | None,
    run: RunResult | None,
    *,
    submode: str,
    scope_id: str | None = None,
    overlay: PlanningOverlayState | None = None,
    type_filters: LCCTypeFilterSet | None = None,
) -> PMChartInput | None:
    if project is None or run is None or run.status != "done":
        return None
    if submode not in ALL_PM_SUBMODES:
        raise ValueError(f"Onbekende PM-submode: {submode!r}")

    overlay_state = overlay or PlanningOverlayState.inactive()
    filters = type_filters or LCCTypeFilterSet.all_on()

    if scope_id is None:
        fm_subset = run.fm_core_results
        pbs_filter = None
    elif scope_id not in project.pbs_items:
        return PMChartInput(submode=submode, scope_id=scope_id, rows=())
    else:
        subtree = collect_pbs_subtree_ids(project, scope_id)
        fm_subset = tuple(fr for fr in run.fm_core_results if fr.pbs_id in subtree)
        pbs_filter = subtree

    num = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    if num <= 0:
        return PMChartInput(submode=submode, scope_id=scope_id, rows=())

    if submode == PM_SUBMODE_KOSTEN:
        curve = build_lcc_planning_curve_reconciled(
            project,
            run,
            scope_id=scope_id,
            overlay=overlay_state,
            type_filters=filters,
        )
        if curve is None:
            return None
        per_year = [float(b.preventief_eur) for b in curve.display_buckets]
    else:
        # Voor aantallen baseren we ons op LTAP-details zodat type_filters (REV, etc.)
        # exact dezelfde selectie doen als in LCC-detail.
        view = get_ltap_view(
            project,
            overlay_anchor_years=overlay_state.anchor_years_dict()
            if overlay_state.active
            else None,
            disabled_pm_ids=overlay_state.disabled_pm_ids
            if overlay_state.active
            else frozenset(),
            fm_pbs_ids=pbs_filter,
        )
        per_year = []
        for year in view.years[:num]:
            count = 0.0
            for detail in year.details:
                task = project.pm_tasks.get(detail.pm_id)
                if task is None or not filters.task_matches(task):
                    continue
                count += float(detail.executions)
            per_year.append(count)

    if len(per_year) < num:
        per_year = per_year + [0.0] * (num - len(per_year))
    per_year = per_year[:num]

    if submode == PM_SUBMODE_KOSTEN:
        # Reconciliatie gebeurt al in build_lcc_planning_curve_reconciled.
        pass

    modeljaar = int(project.config.modeljaar)
    rows: list[PMYearRow] = []
    cumulative = 0.0
    for h, value in enumerate(per_year):
        cumulative += float(value)
        rows.append(
            PMYearRow(
                calendar_year=calendar_year_for_horizon_index(modeljaar, h),
                value=float(value),
                cumulative=cumulative,
            )
        )
    return PMChartInput(submode=submode, scope_id=scope_id, rows=tuple(rows))
