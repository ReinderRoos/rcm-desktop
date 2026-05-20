"""Scalar Top 10-waarden per FM met horizon- en weergave-keuzes (slice 33).

Levert per `FMResult` één getal voor aggregatie in `contribution_chart_service`.
Geen Qt-imports.
"""
from __future__ import annotations

import math
from rcm_core.distributions import (
    build_rev_schedule,
    expected_aging_lifecycle_faalmomenten_ssot,
)
from rcm_core.lcc_profile import (
    expected_faalmomenten_per_bucket_random,
    ltap_horizon_bucket_count,
)
from rcm_core.models import FMResult, RCMProject

from rcm_desktop.adapter.calendar_year import calendar_year_for_horizon_index
from rcm_desktop.adapter.lcc_chart_service import _pm_eur_per_bucket_ltap
from rcm_desktop.adapter.results_workspace_state import (
    ContributionPresentation,
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
)
from rcm_desktop.adapter.unavailability_chart_service import (
    _cor_nb_per_bucket,
    _fm_horizon_context,
)

_HOURS_PER_YEAR = 8760.0


def contribution_value_for_fm(
    project: RCMProject,
    fmr: FMResult,
    *,
    metric: str,
    presentation: ContributionPresentation,
) -> float:
    """Scalar waarde voor één FM in Top 10-aggregatie."""
    if metric == METRIC_KOSTEN:
        return float(fmr.total_cost_eur)
    if metric == METRIC_FAALMOMENTEN:
        return _faalmomenten_scalar(project, fmr, presentation)
    if metric == METRIC_NIET_BESCHIKBAARHEID:
        return _unavailability_scalar(project, fmr, presentation)
    raise ValueError(f"Onbekende metric: {metric!r}")


def _bucket_count(project: RCMProject) -> int:
    return ltap_horizon_bucket_count(float(project.config.lifecycle_years))


def _horizon_index_for_calendar_year(project: RCMProject, calendar_year: int) -> int | None:
    modeljaar = int(project.config.modeljaar)
    idx = int(calendar_year) - modeljaar
    num = _bucket_count(project)
    if 0 <= idx < num:
        return idx
    return None


def _faalmomenten_scalar(
    project: RCMProject,
    fmr: FMResult,
    presentation: ContributionPresentation,
) -> float:
    if presentation.horizon == "lifecycle":
        return float(fmr.expected_failures)
    buckets = _faalmomenten_per_bucket(project, fmr)
    if not buckets:
        return 0.0
    if presentation.year_choice == "average":
        return float(sum(buckets)) / len(buckets)
    idx = _horizon_index_for_calendar_year(project, int(presentation.year_choice))
    if idx is None:
        return 0.0
    return float(buckets[idx])


def _unavailability_scalar(
    project: RCMProject,
    fmr: FMResult,
    presentation: ContributionPresentation,
) -> float:
    lifecycle_hours = float(project.config.lifecycle_years) * _HOURS_PER_YEAR
    total_dt = float(fmr.expected_total_downtime_hr) + float(fmr.expected_pm_downtime_hr)

    if presentation.horizon == "lifecycle":
        if presentation.unavailability_display == "hours":
            return total_dt
        if lifecycle_hours <= 0.0:
            return 0.0
        return (total_dt / lifecycle_hours) * 100.0

    hours_buckets = _nb_hours_per_bucket(project, fmr)
    if not hours_buckets:
        return 0.0

    if presentation.year_choice == "average":
        avg_hr = float(sum(hours_buckets)) / len(hours_buckets)
        if presentation.unavailability_display == "hours":
            return avg_hr
        return (avg_hr / _HOURS_PER_YEAR) * 100.0

    idx = _horizon_index_for_calendar_year(project, int(presentation.year_choice))
    if idx is None:
        return 0.0
    hr = float(hours_buckets[idx])
    if presentation.unavailability_display == "hours":
        return hr
    return (hr / _HOURS_PER_YEAR) * 100.0


def _faalmomenten_per_bucket(project: RCMProject, fmr: FMResult) -> list[float]:
    num = _bucket_count(project)
    if num <= 0:
        return []
    fm = project.faalwijzes.get(fmr.fm_id)
    if fm is None:
        return [0.0] * num
    current_age, lifecycle_end, mult = _fm_horizon_context(project, fmr.pbs_id)
    if fm.failure_type.value == "random":
        moments = expected_faalmomenten_per_bucket_random(
            current_age=current_age,
            lifecycle_end_age=lifecycle_end,
            mttf=float(fm.mttf_jaar),
            multiplicity=mult,
            num_buckets=num,
        )
    else:
        pm_for_fm = [t for t in project.pm_tasks.values() if t.fm_id == fmr.fm_id]
        _, moments_u = expected_aging_lifecycle_faalmomenten_ssot(
            current_age=current_age,
            lifecycle_years=lifecycle_end,
            mttf=float(fm.mttf_jaar),
            sigma=float(fm.effective_sigma),
            repair_quality=float(fm.repair_quality),
            num_buckets=num,
            rev_schedule=build_rev_schedule(pm_for_fm),
        )
        moments = [float(m) * mult for m in moments_u]
    out = [0.0] * num
    for h, mh in enumerate(moments):
        if h < num:
            out[h] = float(mh)
    return out


def _nb_hours_per_bucket(project: RCMProject, fmr: FMResult) -> list[float]:
    """CM + hidden NB + PM downtime per horizonbucket, gereconcilieerd naar lifecycle."""
    num = _bucket_count(project)
    if num <= 0:
        return []
    cm_dt, hidden_nb, used_legacy = _cor_nb_per_bucket(project, (fmr,), num)
    target_pm_dt = float(fmr.expected_pm_downtime_hr)
    pm_dt = (
        _pm_eur_per_bucket_ltap(project, target_pm_dt)
        if target_pm_dt > 0
        else [0.0] * num
    )
    if len(pm_dt) < num:
        pm_dt = pm_dt + [0.0] * (num - len(pm_dt))
    pm_dt = pm_dt[:num]

    combined = [
        float(cm_dt[i]) + float(hidden_nb[i]) + float(pm_dt[i]) for i in range(num)
    ]
    target_total = float(fmr.expected_total_downtime_hr) + target_pm_dt
    got = float(sum(combined))
    if used_legacy and got > 0.0 and not math.isclose(got, target_total, rel_tol=0, abs_tol=1e-5):
        scale = target_total / got
        combined = [v * scale for v in combined]
    elif got == 0.0 and target_total != 0.0 and num > 0:
        combined[0] = target_total
    return combined


def calendar_years_for_project(project: RCMProject) -> tuple[int, ...]:
    """Kalenderjaren in de lifecycle-horizon (voor jaarkiezer)."""
    num = _bucket_count(project)
    modeljaar = int(project.config.modeljaar)
    return tuple(
        calendar_year_for_horizon_index(modeljaar, h) for h in range(num)
    )
