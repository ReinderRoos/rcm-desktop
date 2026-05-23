"""Horizon bucket series — public adapter seam for per-bucket presentatie."""

from __future__ import annotations

from collections.abc import Sequence

from rcm_core.distributions import (
    build_rev_schedule,
    expected_aging_lifecycle_faalmomenten_ssot,
)
from rcm_core.lcc_profile import (
    expected_faalmomenten_per_bucket_random,
    ltap_horizon_bucket_count,
)
from rcm_core.models import FMResult, RCMProject

from rcm_desktop.adapter.ltap_execution_schedule import ltap_executions_by_year


def fm_horizon_context(project: RCMProject, pbs_id: str) -> tuple[float, float, float]:
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


def faalmomenten_per_bucket(project: RCMProject, fmr: FMResult) -> list[float]:
    """Verwachte faalmomenten per horizonbucket voor één FM."""
    num = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    if num <= 0:
        return []
    fm = project.faalwijzes.get(fmr.fm_id)
    if fm is None:
        return [0.0] * num
    current_age, lifecycle_end, mult = fm_horizon_context(project, fmr.pbs_id)
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


def motor_cor_eur_per_bucket(fmr: FMResult, num: int) -> list[float]:
    """Correctief EUR per bucket uit motor-`horizon_profile`; leeg bij ontbrekend profiel."""
    hp = fmr.horizon_profile
    if hp is None:
        return []
    out = [float(v) for v in hp.cor_eur]
    while len(out) < num:
        out.append(0.0)
    return out[:num]


def motor_cor_downtime_per_bucket(fmr: FMResult, num: int) -> list[float]:
    hp = fmr.horizon_profile
    if hp is None:
        return []
    out = [float(v) for v in hp.cor_downtime_hr]
    while len(out) < num:
        out.append(0.0)
    return out[:num]


def motor_hidden_nb_per_bucket(fmr: FMResult, num: int) -> list[float]:
    hp = fmr.horizon_profile
    if hp is None:
        return []
    out = [float(v) for v in hp.hidden_nb_hr]
    while len(out) < num:
        out.append(0.0)
    return out[:num]


def cor_nb_per_bucket(
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
    moments = faalmomenten_per_bucket(project, fr)
    msum = float(sum(moments))
    dt_total = float(fr.expected_total_downtime_hr)
    if msum <= 0:
        if dt_total != 0.0 and num > 0:
            out[0] = dt_total
        return out
    for h, mh in enumerate(moments):
        if h < num:
            out[h] = dt_total * (float(mh) / msum)
    return out
