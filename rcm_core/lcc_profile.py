"""Lifecycle-kosten jaarbuckets (LCC): correctief (faalgebonden) verdeeld naar verwachte
faalmomenten per horizonjaar.

Horizonindex h (0 …) deelt hetzelfde raster als LTAP: aantal buckets = ceil(lifecycle_years).
Overlap [current_age+h, current_age+h+1) ∩ [current_age, lifecycle_end) meet hoeveel
modeljaar-tijd in bucket h valt — gelijk aan LTAP's interpretatie van horizonjaren t.o.v.
config.lifecycle_years (eindleeftijd / studiegrens zoals de motor gebruikt in
`expected_failures_lifecycle`). Voor **aging** komen de verwachte faalmomenten per jaar uit
**dezelfde** aging-SSOT als de motor (iteraties met ``repair_quality``; Φ-segmenten per bucket);
voor **random** blijft het exponentiële (constante hazard) pad.
"""

from __future__ import annotations

import math
from typing import Sequence

from rcm_core.distributions import (
    build_rev_schedule,
    expected_aging_lifecycle_faalmomenten_ssot,
)
from rcm_core.models import FMResult, RCMProject


def ltap_horizon_bucket_count(lifecycle_years: float) -> int:
    """Aantal horizonjaren gelijk aan LTAP (`max(0, ceil(L))` buckets)."""
    max_year = max(0, math.ceil(float(lifecycle_years)) - 1)
    return max_year + 1


def overlap_years_per_bucket(
    current_age: float,
    lifecycle_end_age: float,
    num_buckets: int,
) -> list[float]:
    """Overlap in 'leeftijd-jaren' tussen bucket h en het analysevenster."""
    out: list[float] = []
    for h in range(num_buckets):
        start = current_age + float(h)
        end = current_age + float(h) + 1.0
        hi = max(0.0, min(end, lifecycle_end_age) - max(start, current_age))
        out.append(hi)
    return out


def expected_faalmomenten_per_bucket_random(
    *,
    current_age: float,
    lifecycle_end_age: float,
    mttf: float,
    multiplicity: float,
    num_buckets: int,
) -> list[float]:
    """Exponentieel (random): verwachte faalmomenten ∝ overlap / MTTF per bucket."""
    overlaps = overlap_years_per_bucket(current_age, lifecycle_end_age, num_buckets)
    if mttf <= 0:
        return [0.0] * num_buckets
    return [float(multiplicity) * oh / mttf for oh in overlaps]


def expected_faalmomenten_per_bucket_proportional(
    *,
    total_expected_failures: float,
    overlaps: Sequence[float],
) -> list[float]:
    """Verdeel totaal verwachte faalmomenten proportioneel aan overlap (o.a. aging-approx)."""
    s = float(sum(overlaps))
    if s <= 0:
        return [0.0] * len(overlaps)
    return [total_expected_failures * float(oh) / s for oh in overlaps]


def _fm_horizon_context(project: RCMProject, _fm_id: str, pbs_id: str) -> tuple[float, float, float]:
    """(current_age, lifecycle_end_age, multiplicity) — zelfde semantiek als compute_fm_result."""
    pbs = project.pbs_items.get(pbs_id)
    if pbs is None:
        return 0.0, float(project.config.lifecycle_years), 1.0
    all_pbs = project.pbs_items
    if all_pbs is not None:
        eff_bouwjaar = pbs.effective_bouwjaar(all_pbs)
        current_age = float(project.config.modeljaar - eff_bouwjaar) if eff_bouwjaar > 0 else 0.0
        eff_mult = float(pbs.effective_multiplicity(all_pbs))
    else:
        current_age = float(pbs.current_age(project.config.modeljaar))
        eff_mult = float(pbs.multiplicity)
    lifecycle_end = float(project.config.lifecycle_years)
    return current_age, lifecycle_end, eff_mult


def _legacy_cm_eur_per_fm(
    project: RCMProject,
    fr: FMResult,
    num: int,
    cm: list[float],
) -> None:
    """Proportionele verdeling (cache-migratie / ontbrekend horizonprofiel)."""
    fm = project.faalwijzes.get(fr.fm_id)
    if fm is None:
        return
    current_age, lifecycle_end, mult = _fm_horizon_context(project, fr.fm_id, fr.pbs_id)
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
    cm_cost = float(fr.expected_cm_cost_eur)
    if msum <= 0:
        if cm_cost != 0.0 and num > 0:
            cm[0] += cm_cost
        return
    for h, mh in enumerate(moments):
        cm[h] += cm_cost * (float(mh) / msum)


def build_cor_eur_per_bucket(
    project: RCMProject,
    fm_results: Sequence[FMResult],
) -> tuple[list[float], bool]:
    """Projecttotaal correctief EUR per horizonindex uit motorprofielen.

    Returns ``(buckets, used_legacy_fallback)``.
    """
    num = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    cor = [0.0] * num
    used_legacy = False
    for fr in fm_results:
        hp = fr.horizon_profile
        if hp is not None and len(hp.cor_eur) >= num:
            for h in range(num):
                cor[h] += float(hp.cor_eur[h])
        elif hp is not None and len(hp.cor_eur) > 0:
            for h in range(min(num, len(hp.cor_eur))):
                cor[h] += float(hp.cor_eur[h])
        else:
            used_legacy = True
            _legacy_cm_eur_per_fm(project, fr, num, cor)
    target = sum(float(r.expected_cm_cost_eur) for r in fm_results)
    got = float(sum(cor))
    if used_legacy and got > 0 and not math.isclose(got, target, rel_tol=0, abs_tol=1e-5):
        scale = target / got
        cor = [float(v) * scale for v in cor]
    elif got == 0.0 and target != 0.0 and num > 0:
        cor[0] = target
    return cor, used_legacy


def build_cm_eur_per_bucket(project: RCMProject, fm_results: Sequence[FMResult]) -> list[float]:
    """Alias: jaarlijkse correctief EUR (``cor_eur``); zie :func:`build_cor_eur_per_bucket`."""
    buckets, _ = build_cor_eur_per_bucket(project, fm_results)
    return buckets
