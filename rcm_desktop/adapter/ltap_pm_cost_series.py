"""LTAP PM-totalen zonder task-detail objecten (slice 38 light path)."""
from __future__ import annotations

import math

from rcm_core.lcc_profile import ltap_horizon_bucket_count
from rcm_core.models import RCMProject

from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.ltap_service import _executions_by_year


def build_ltap_pm_cost_series(
    project: RCMProject,
    *,
    overlay_anchor_years: dict[str, float] | None = None,
    disabled_pm_ids: frozenset[str] | None = None,
    fm_pbs_ids: frozenset[str] | None = None,
    type_filters: LCCTypeFilterSet | None = None,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Per horizon-index (raw PM, type-filter-unie PM) zonder LTAPTaskDetail."""
    lifecycle_years = float(project.config.lifecycle_years)
    n = ltap_horizon_bucket_count(lifecycle_years)
    raw = [0.0] * n
    filtered = [0.0] * n
    disabled = disabled_pm_ids or frozenset()
    filters = type_filters or LCCTypeFilterSet.all_on()
    anchors = overlay_anchor_years or {}

    for task in sorted(project.pm_tasks.values(), key=lambda item: item.pm_id):
        if task.pm_id in disabled:
            continue
        if fm_pbs_ids is not None:
            fm = project.faalwijzes.get(task.fm_id)
            if fm is None or fm.pbs_id not in fm_pbs_ids:
                continue
        anchor_year = float(anchors.get(task.pm_id, 0.0))
        executions_by_year = _executions_by_year(
            task,
            lifecycle_years=lifecycle_years,
            anchor_year=anchor_year,
        )
        matches_filter = filters.task_matches(task)
        for year, executions in executions_by_year.items():
            if executions <= 0 or not (0 <= year < n):
                continue
            cost = float(task.cost_eur) * executions
            raw[year] += cost
            if matches_filter:
                filtered[year] += cost

    return tuple(raw), tuple(filtered)
