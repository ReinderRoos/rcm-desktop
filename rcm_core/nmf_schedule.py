"""NMF-jaarpad: ontdekking, verborgen NB en uitgestelde correctieve toerekening (slice 27)."""
from __future__ import annotations

import math

from rcm_core.distributions import rejuvenate_age


def next_test_time_years(failure_time_years: float, test_intervals_years: list[float]) -> float:
    """Eerstvolgende geplande test op of na ``failure_time_years`` (union-grid minimum)."""
    if not test_intervals_years:
        return float("inf")
    best = float("inf")
    t = max(0.0, float(failure_time_years))
    for interval in test_intervals_years:
        iv = float(interval)
        if iv <= 0.0:
            continue
        if t <= 1e-12:
            candidate = 0.0
        else:
            n = math.ceil(t / iv - 1e-12)
            candidate = n * iv
            if candidate < t - 1e-12:
                candidate = (n + 1) * iv
        best = min(best, candidate)
    return best


def age_after_nmf_discovery(
    *,
    study_start_age: float,
    discovery_study_year: float,
    repair_quality: float,
) -> float:
    """Effectieve leeftijd na correctief herstel bij NMF-ontdekking (zelfde semantiek als evident CM)."""
    age_at_discovery = study_start_age + float(discovery_study_year)
    return rejuvenate_age(age_at_discovery, repair_quality)


def build_horizon_profile(
    *,
    faalmomenten: list[float],
    is_evident: bool,
    test_intervals_years: list[float],
    cost_per_failure_eur: float,
    downtime_per_failure_hr: float,
    num_buckets: int,
) -> tuple[list[float], list[float], list[float]]:
    """Bouw ``cor_eur``, ``cor_downtime_hr`` en ``hidden_nb_hr`` per horizonbucket."""
    cor_eur = [0.0] * num_buckets
    cor_downtime_hr = [0.0] * num_buckets
    hidden_nb_hr = [0.0] * num_buckets

    for h, mass in enumerate(faalmomenten):
        if mass <= 0.0 or h >= num_buckets:
            continue
        m = float(mass)
        if is_evident:
            cor_eur[h] += cost_per_failure_eur * m
            cor_downtime_hr[h] += downtime_per_failure_hr * m
            continue

        t_fail = float(h) + 0.5
        t_disc = next_test_time_years(t_fail, test_intervals_years)
        if not math.isfinite(t_disc):
            continue
        if t_disc <= t_fail + 1e-12:
            disc_bucket = min(h, num_buckets - 1)
            cor_eur[disc_bucket] += cost_per_failure_eur * m
            cor_downtime_hr[disc_bucket] += downtime_per_failure_hr * m
            continue

        period_lo, period_hi = t_fail, t_disc
        period_len = period_hi - period_lo
        hidden_total = downtime_per_failure_hr * m
        for k in range(num_buckets):
            bucket_lo = float(k)
            bucket_hi = float(k) + 1.0
            overlap = max(0.0, min(bucket_hi, period_hi) - max(bucket_lo, period_lo))
            if overlap > 0.0:
                hidden_nb_hr[k] += hidden_total * (overlap / period_len)

        disc_bucket = min(int(math.floor(t_disc + 1e-9)), num_buckets - 1)
        cor_eur[disc_bucket] += cost_per_failure_eur * m
        cor_downtime_hr[disc_bucket] += downtime_per_failure_hr * m

    return cor_eur, cor_downtime_hr, hidden_nb_hr
