"""Qt-vrije adapter: proxy-jaarverdeling van niet-beschikbaarheid (slice 23
fase D — issue 04).

Bouwt een tuple `UnavailabilityYearRow` per kalenderjaar voor de horizon van
het project. De verdeling **proxieert** de jaarlijkse downtime door dezelfde
aging-/random-pipeline te volgen die de correctieve LCC-jaarverdeling gebruikt
(`rcm_core.lcc_profile.build_cm_eur_per_bucket`). Het **lifecycle-totaal**
reconcilieert exact (1e-3) tegen de motor-output: voor `scope_id=None` tegen
`RunMetrics.total_downtime_hr`, voor een subtree-scope tegen het gesommeerde
subtree-totaal van `expected_total_downtime_hr + expected_pm_downtime_hr` over
de FM's onder die subtree.

Belangrijk: dit is een **presentatie-proxy**. De motor levert lifecycle-
totaal-juiste cijfers; de jaarverdeling is een visualisatie-hulp en kan
voor zeldzame aging-FMs in randjaren afwijken van een Monte-Carlo-resultaat.
De view-laag toont dit als disclaimer.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

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
from rcm_desktop.adapter.run_service import RunResult

_HOURS_PER_YEAR = 8760.0


@dataclass(frozen=True)
class UnavailabilityYearRow:
    calendar_year: int
    unavailability_pct: float
    downtime_hr: float


@dataclass(frozen=True)
class UnavailabilityChartInput:
    scope_id: str | None
    rows: tuple[UnavailabilityYearRow, ...]


def build_unavailability_chart_input(
    project: RCMProject | None,
    run: RunResult | None,
    *,
    scope_id: str | None = None,
) -> UnavailabilityChartInput | None:
    """Bouw de jaar-rijen voor de niet-beschikbaarheid-modus.

    Geeft `None` als het project ontbreekt, de run niet voltooid is, of er
    geen kern-FM-resultaten beschikbaar zijn.
    """
    if project is None or run is None or run.status != "done" or not run.fm_core_results:
        return None

    if scope_id is None:
        fm_subset: Sequence[FMResult] = run.fm_core_results
    else:
        if scope_id not in project.pbs_items:
            return UnavailabilityChartInput(scope_id=scope_id, rows=())
        subtree = _collect_subtree_ids(project, scope_id)
        fm_subset = tuple(fr for fr in run.fm_core_results if fr.pbs_id in subtree)
        if not fm_subset:
            return UnavailabilityChartInput(scope_id=scope_id, rows=())

    num = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    if num <= 0:
        return UnavailabilityChartInput(scope_id=scope_id, rows=())

    cm_dt, hidden_nb, used_legacy = _cor_nb_per_bucket(project, fm_subset, num)

    target_pm_dt = sum(float(fr.expected_pm_downtime_hr) for fr in fm_subset)
    pm_dt = _pm_eur_per_bucket_ltap(project, target_pm_dt) if target_pm_dt > 0 else [0.0] * num
    if len(pm_dt) < num:
        pm_dt = pm_dt + [0.0] * (num - len(pm_dt))
    pm_dt = pm_dt[:num]

    combined = [
        float(cm_dt[i]) + float(hidden_nb[i]) + float(pm_dt[i]) for i in range(num)
    ]

    target_total = sum(
        float(fr.expected_total_downtime_hr) + float(fr.expected_pm_downtime_hr)
        for fr in fm_subset
    )
    got = float(sum(combined))
    if used_legacy and got > 0.0 and not math.isclose(got, target_total, rel_tol=0, abs_tol=1e-5):
        scale = target_total / got
        combined = [v * scale for v in combined]
    elif got == 0.0 and target_total != 0.0 and num > 0:
        combined[0] = target_total

    modeljaar = int(project.config.modeljaar)
    rows = tuple(
        UnavailabilityYearRow(
            calendar_year=calendar_year_for_horizon_index(modeljaar, h),
            downtime_hr=combined[h],
            unavailability_pct=(combined[h] / _HOURS_PER_YEAR) * 100.0,
        )
        for h in range(num)
    )
    return UnavailabilityChartInput(scope_id=scope_id, rows=rows)


def _cor_nb_per_bucket(
    project: RCMProject,
    fm_results: Sequence[FMResult],
    num: int,
) -> tuple[list[float], list[float], bool]:
    """``cor_downtime_hr`` en ``hidden_nb_hr`` per bucket; legacy-flag bij ontbrekend profiel."""
    cor_dt = [0.0] * num
    hidden = [0.0] * num
    used_legacy = False
    for fr in fm_results:
        hp = fr.horizon_profile
        if hp is not None:
            for h in range(min(num, len(hp.cor_downtime_hr))):
                cor_dt[h] += float(hp.cor_downtime_hr[h])
            for h in range(min(num, len(hp.hidden_nb_hr))):
                hidden[h] += float(hp.hidden_nb_hr[h])
        else:
            used_legacy = True
            legacy_dt = _legacy_cm_downtime_per_fm(project, fr, num)
            for h in range(num):
                cor_dt[h] += legacy_dt[h]
    return cor_dt, hidden, used_legacy


def _legacy_cm_downtime_per_fm(
    project: RCMProject,
    fr: FMResult,
    num: int,
) -> list[float]:
    """Proportionele correctief-downtime (cache-migratie)."""
    out = [0.0] * num
    fm = project.faalwijzes.get(fr.fm_id)
    if fm is None:
        return out
    current_age, lifecycle_end, mult = _fm_horizon_context(project, fr.pbs_id)
    if fm.failure_type.value == "random":
        moments = expected_faalmomenten_per_bucket_random(
            current_age=current_age,
            lifecycle_end_age=lifecycle_end,
            mttf=float(fm.mttf_jaar),
            multiplicity=mult,
            num_buckets=num,
        )
    else:
        pm_for_fm = [t for t in project.pm_tasks.values() if t.fm_id == fr.fm_id]
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
    msum = float(sum(moments))
    dt_total = float(fr.expected_total_downtime_hr)
    if msum <= 0:
        if dt_total != 0.0 and num > 0:
            out[0] = dt_total
        return out
    for h, mh in enumerate(moments):
        out[h] = dt_total * (float(mh) / msum)
    return out


def _cm_downtime_per_bucket(
    project: RCMProject,
    fm_results: Sequence[FMResult],
    num: int,
) -> list[float]:
    """Verdeel correctief-downtime over buckets (legacy helper; gebruik ``_cor_nb_per_bucket``)."""
    out = [0.0] * num
    for fr in fm_results:
        fm = project.faalwijzes.get(fr.fm_id)
        if fm is None:
            continue
        current_age, lifecycle_end, mult = _fm_horizon_context(project, fr.pbs_id)
        if fm.failure_type.value == "random":
            moments = expected_faalmomenten_per_bucket_random(
                current_age=current_age,
                lifecycle_end_age=lifecycle_end,
                mttf=float(fm.mttf_jaar),
                multiplicity=mult,
                num_buckets=num,
            )
        else:
            pm_for_fm = [t for t in project.pm_tasks.values() if t.fm_id == fr.fm_id]
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
        msum = float(sum(moments))
        dt_total = float(fr.expected_total_downtime_hr)
        if msum <= 0:
            if dt_total != 0.0 and num > 0:
                out[0] += dt_total
            continue
        for h, mh in enumerate(moments):
            out[h] += dt_total * (float(mh) / msum)
    return out


def _fm_horizon_context(project: RCMProject, pbs_id: str) -> tuple[float, float, float]:
    """(current_age, lifecycle_end_age, multiplicity) — zelfde semantiek als `lcc_profile`."""
    pbs = project.pbs_items.get(pbs_id)
    if pbs is None:
        return 0.0, float(project.config.lifecycle_years), 1.0
    all_pbs = project.pbs_items
    eff_bouwjaar = pbs.effective_bouwjaar(all_pbs)
    current_age = (
        float(project.config.modeljaar - eff_bouwjaar) if eff_bouwjaar > 0 else 0.0
    )
    eff_mult = float(pbs.effective_multiplicity(all_pbs))
    lifecycle_end = float(project.config.lifecycle_years)
    return current_age, lifecycle_end, eff_mult


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
