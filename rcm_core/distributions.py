"""
distributions.py — Verdelingswiskunde voor faalkansberekeningen.

Alle functies zijn pure wiskunde: geen I/O, geen modelobjecten.
lru_cache voorkomt herberekening bij identieke parameters (veel FM's delen MTTF/sigma).

Tijdseenheden: jaren (leeftijden, MTTF, lifecycle). Uren alleen in conversies elders.
"""
from __future__ import annotations
import math
from functools import lru_cache
from typing import TYPE_CHECKING

import numpy as np
from scipy import stats

from rcm_core.normal_fast import normal_cdf, truncated_normal_conditional_mean

if TYPE_CHECKING:
    from rcm_core.models import PMTask

RevSchedule = tuple[tuple[float, float], ...]


def _weibull_eta_from_mttf_beta(mttf: float, beta: float) -> float:
    if mttf <= 0.0 or beta <= 0.0:
        return 0.0
    return float(mttf) / float(math.gamma(1.0 + (1.0 / float(beta))))


def _weibull_cdf(age: float, *, mttf: float, beta: float) -> float:
    if age <= 0.0:
        return 0.0
    eta = _weibull_eta_from_mttf_beta(mttf, beta)
    if eta <= 0.0:
        return 0.0
    return 1.0 - math.exp(-((float(age) / eta) ** float(beta)))


def _truncated_normal_0_cdf(age: float, *, mttf: float, sigma: float) -> float:
    if sigma <= 0.0:
        return 0.0
    if age <= 0.0:
        return 0.0
    f_age = float(normal_cdf(float(age), float(mttf), float(sigma)))
    f_zero = float(normal_cdf(0.0, float(mttf), float(sigma)))
    denom = 1.0 - f_zero
    if denom <= 1e-12:
        return 0.0
    return max(0.0, min(1.0, (f_age - f_zero) / denom))


# ---------------------------------------------------------------------------
# Faalkansberekeningen
# ---------------------------------------------------------------------------

@lru_cache(maxsize=2048)
def p_failure_by_age(
    t: float,
    failure_type: str,
    mttf: float,
    sigma: float,
    aging_distribution: str = "normal",
    beta_jaar: float = 0.0,
) -> float:
    """P(asset heeft gefaald vóór leeftijd t) — cumulatieve faalkans.

    random: exponentiaalverdeling, P = 1 - exp(-t/MTTF)
    aging:  normaalverdeling,      P = Φ((t - MTTF) / sigma)
    """
    if mttf <= 0:
        return 0.0
    if failure_type == "random":
        return 1.0 - math.exp(-t / mttf)
    elif failure_type == "aging":
        dist = str(aging_distribution or "normal")
        if dist == "weibull_2p":
            return _weibull_cdf(t, mttf=mttf, beta=beta_jaar)
        if sigma <= 0:
            return 0.0
        if dist == "truncated_normal_0":
            return _truncated_normal_0_cdf(t, mttf=mttf, sigma=sigma)
        return float(stats.norm.cdf(t, loc=mttf, scale=sigma))
    else:
        raise ValueError(f"Onbekend failure_type: {failure_type!r}")


def effective_age_after_repair(age_at_failure: float, repair_quality: float) -> float:
    """Effectieve leeftijd na reparatie.

    repair_quality=1.0 → as good as new  (leeftijd=0)
    repair_quality=0.0 → as good as old  (leeftijd ongewijzigd)
    repair_quality=0.3 → 30% nieuw: leeftijd × (1 - 0,3) = 0,7 × leeftijd

    Voorbeeld: 10 jaar oud, 30% nieuw → 7 jaar effectief.
    """
    return age_at_failure * (1.0 - repair_quality)


def expected_failures_lifecycle(
    current_age: float,
    lifecycle_years: float,
    failure_type: str,
    mttf: float,
    sigma: float,
    repair_quality: float,
    aging_distribution: str = "normal",
    beta_jaar: float = 0.0,
    rev_schedule: RevSchedule = (),
) -> float:
    """Verwacht aantal falingen gedurende de modelleerperiode.

    Voor random falen: (lifecycle_years - current_age) / mttf
      — exponentiaalverdeling is geheugenloos, huidige leeftijd doet er niet toe.

    Voor aging falen: numerieke integratie.
      Na elke faling wordt de effectieve leeftijd bijgesteld op basis van repair_quality.
      De integratie loopt door totdat het einde van de lifecycle bereikt is.
    """
    if mttf <= 0:
        return 0.0

    remaining = lifecycle_years - current_age
    if remaining <= 0:
        return 0.0

    if failure_type == "random":
        return remaining / mttf

    if str(aging_distribution or "normal") == "weibull_2p":
        f_start = _weibull_cdf(current_age, mttf=mttf, beta=beta_jaar)
        f_end = _weibull_cdf(lifecycle_years, mttf=mttf, beta=beta_jaar)
        survival_start = 1.0 - f_start
        if survival_start <= 1e-10:
            return 0.0
        return max(0.0, (f_end - f_start) / survival_start)

    total, _ = expected_aging_lifecycle_faalmomenten_ssot(
        current_age=current_age,
        lifecycle_years=lifecycle_years,
        mttf=mttf,
        sigma=sigma,
        repair_quality=repair_quality,
        aging_distribution=aging_distribution,
        beta_jaar=beta_jaar,
        num_buckets=0,
        rev_schedule=rev_schedule,
    )
    return total


# ---------------------------------------------------------------------------
# Monte Carlo sampling
# ---------------------------------------------------------------------------

def sample_time_to_failure(
    current_age: float,
    failure_type: str,
    mttf: float,
    sigma: float,
    rng: np.random.Generator,
    aging_distribution: str = "normal",
    beta_jaar: float = 0.0,
) -> float:
    """Trek één steekproef van de tijd-tot-falen.

    random: exponentiaal, geheugenloos (current_age genegeerd)
    aging:  afgeknipte normaalverdeling vanaf current_age
            via: t = F^-1( F(current_age) + u × (1 - F(current_age)) )
            waarbij u ~ Uniform(0,1)
    """
    if failure_type == "random":
        return float(rng.exponential(scale=mttf))

    elif failure_type == "aging":
        dist = str(aging_distribution or "normal")
        if dist == "weibull_2p":
            eta = _weibull_eta_from_mttf_beta(mttf, beta_jaar)
            if eta <= 0.0:
                return current_age
            f_current = _weibull_cdf(current_age, mttf=mttf, beta=beta_jaar)
            survival = 1.0 - f_current
            if survival < 1e-10:
                return current_age
            u = rng.uniform(0.0, 1.0)
            p = f_current + u * survival
            p = min(p, 1.0 - 1e-12)
            return float(eta * ((-math.log(1.0 - p)) ** (1.0 / float(beta_jaar))))
        if sigma <= 0:
            sigma = 0.15 * mttf
        if dist == "truncated_normal_0":
            f_current = _truncated_normal_0_cdf(current_age, mttf=mttf, sigma=sigma)
            survival = 1.0 - f_current
            if survival < 1e-10:
                return current_age
            u = rng.uniform(0.0, 1.0)
            p = f_current + u * survival
            p = min(p, 1.0 - 1e-12)
            phi0 = float(normal_cdf(0.0, mttf, sigma))
            p_untruncated = phi0 + p * (1.0 - phi0)
            return float(stats.norm.ppf(p_untruncated, loc=mttf, scale=sigma))
        f_current = stats.norm.cdf(current_age, loc=mttf, scale=sigma)
        survival = 1.0 - f_current
        if survival < 1e-10:
            # Asset praktisch zeker al gefaald — geef huidige leeftijd terug
            return current_age
        u = rng.uniform(0.0, 1.0)
        # Inverse CDF van de afgeknipte verdeling
        p = f_current + u * survival
        p = min(p, 1.0 - 1e-12)  # voorkom norm.ppf(1) = inf
        return float(stats.norm.ppf(p, loc=mttf, scale=sigma))

    else:
        raise ValueError(f"Onbekend failure_type: {failure_type!r}")


# ---------------------------------------------------------------------------
# REV / kalenderbuckets (slice 22/24 — aging SSOT)
# ---------------------------------------------------------------------------


def rejuvenate_age(age: float, effect_fraction: float) -> float:
    """Gedeeld voor CM (repair_quality) en REV (aging_effect_pct/100)."""
    return age * (1.0 - effect_fraction)


def build_rev_schedule(pm_tasks: list["PMTask"]) -> RevSchedule:
    """(interval_jaar, effect_fraction) voor REV-taken, gesorteerd op interval."""
    from rcm_core.models import TaskType

    entries: list[tuple[float, float]] = []
    for task in pm_tasks:
        if task.taak_type == TaskType.REV and float(task.interval_jaar) > 0:
            effect = float(getattr(task, "aging_effect_pct", 100.0)) / 100.0
            entries.append((float(task.interval_jaar), effect))
    return tuple(sorted(entries, key=lambda item: item[0]))


def _conditional_failures_with_rev_segments(
    effective_age: float,
    *,
    clock_start: float,
    rem_clock: float,
    mttf: float,
    sigma: float,
    aging_distribution: str = "normal",
    beta_jaar: float = 0.0,
    rev_schedule: RevSchedule,
) -> float:
    """Verwachte faalmomenten tot studie-einde met REV op kalendergrenzen."""
    if rem_clock <= 0:
        return 0.0

    clock_end = clock_start + rem_clock
    if str(aging_distribution or "normal") == "weibull_2p":
        f_at_start = _weibull_cdf(effective_age, mttf=mttf, beta=beta_jaar)
    elif str(aging_distribution or "normal") == "truncated_normal_0":
        f_at_start = _truncated_normal_0_cdf(effective_age, mttf=mttf, sigma=sigma)
    else:
        f_at_start = float(normal_cdf(effective_age, mttf, sigma))
    survival = 1.0 - f_at_start
    if survival < 1e-10:
        return 0.0

    if not rev_schedule:
        age_end = effective_age + rem_clock
        if str(aging_distribution or "normal") == "weibull_2p":
            f_end = _weibull_cdf(age_end, mttf=mttf, beta=beta_jaar)
        elif str(aging_distribution or "normal") == "truncated_normal_0":
            f_end = _truncated_normal_0_cdf(age_end, mttf=mttf, sigma=sigma)
        else:
            f_end = float(normal_cdf(age_end, mttf, sigma))
        return (f_end - f_at_start) / survival

    events: list[tuple[float, float]] = []
    for interval, effect_fraction in rev_schedule:
        if interval <= 1e-15:
            continue
        k = int(math.floor(clock_start / interval)) + 1
        while True:
            t = k * interval
            if t > clock_end + 1e-9:
                break
            if t > clock_start + 1e-9:
                events.append((t, float(effect_fraction)))
            k += 1
    events.sort(key=lambda item: item[0])

    grouped: list[tuple[float, list[float]]] = []
    i = 0
    while i < len(events):
        t0 = events[i][0]
        effects = [events[i][1]]
        i += 1
        while i < len(events) and abs(events[i][0] - t0) < 1e-9:
            effects.append(events[i][1])
            i += 1
        grouped.append((t0, effects))

    boundaries = [float(clock_start)] + [t for t, _ in grouped] + [float(clock_end)]
    age = float(effective_age)
    total = 0.0
    rev_idx = 0
    for bi in range(len(boundaries) - 1):
        b0, b1 = boundaries[bi], boundaries[bi + 1]
        if b1 <= b0 + 1e-15:
            continue
        age_end = age + (b1 - b0)
        if str(aging_distribution or "normal") == "weibull_2p":
            f_lo = _weibull_cdf(age, mttf=mttf, beta=beta_jaar)
            f_hi = _weibull_cdf(age_end, mttf=mttf, beta=beta_jaar)
        elif str(aging_distribution or "normal") == "truncated_normal_0":
            f_lo = _truncated_normal_0_cdf(age, mttf=mttf, sigma=sigma)
            f_hi = _truncated_normal_0_cdf(age_end, mttf=mttf, sigma=sigma)
        else:
            f_lo = float(normal_cdf(age, mttf, sigma))
            f_hi = float(normal_cdf(age_end, mttf, sigma))
        total += (f_hi - f_lo) / survival
        age = age_end
        if rev_idx < len(grouped) and abs(b1 - grouped[rev_idx][0]) < 1e-9:
            for effect in grouped[rev_idx][1]:
                age = rejuvenate_age(age, effect)
            rev_idx += 1
    return total


def apply_rev_along_calendar_segment(
    effective_age: float,
    *,
    clock_start: float,
    clock_end: float,
    rev_schedule: RevSchedule,
) -> float:
    """Lineair verouderen over ``[clock_start, clock_end]`` met REV op interval-grenzen."""
    if not rev_schedule or clock_end <= clock_start + 1e-15:
        return float(effective_age)

    events: list[tuple[float, float]] = []
    for interval, effect_fraction in rev_schedule:
        if interval <= 1e-15:
            continue
        k = int(math.floor(clock_start / interval)) + 1
        while True:
            t = k * interval
            if t > clock_end + 1e-9:
                break
            if t > clock_start + 1e-9:
                events.append((t, float(effect_fraction)))
            k += 1
    events.sort(key=lambda item: item[0])

    age = float(effective_age)
    t_cursor = float(clock_start)
    i = 0
    while i < len(events):
        rev_t = events[i][0]
        age += rev_t - t_cursor
        while i < len(events) and abs(events[i][0] - rev_t) < 1e-9:
            age = rejuvenate_age(age, events[i][1])
            i += 1
        t_cursor = rev_t
    age += float(clock_end) - t_cursor
    return age


def expected_aging_lifecycle_faalmomenten_ssot(
    *,
    current_age: float,
    lifecycle_years: float,
    mttf: float,
    sigma: float,
    aging_distribution: str = "normal",
    beta_jaar: float = 0.0,
    repair_quality: float,
    num_buckets: int,
    rev_schedule: RevSchedule = (),
    max_iterations: int = 100,
) -> tuple[float, list[float]]:
    """Eén aging-pad: totaal verwachte faalmomenten én per kalenderjaarbucket.

    Per iteratie wordt ``p_fails_before_end`` over **studiejaar-buckets** ``[h, h+1)``
    verdeeld via Φ-segmenten: leeftijdsinterval ``[effective_age, age_at_lifecycle_end]``
    wordt affien teruggemapt naar ``[clock_time, clock_time + rem_clock]``.

    ``num_buckets <= 0``: lege lijst, alleen totaal (licht pad voor lifecycle-totaal).
    """
    if mttf <= 0:
        return 0.0, [0.0] * max(0, num_buckets)

    study_start_age = float(current_age)
    lifecycle_study_end = float(lifecycle_years)
    study_duration = lifecycle_study_end - study_start_age
    if study_duration <= 0:
        return 0.0, [0.0] * max(0, num_buckets)

    sig = float(sigma)
    if sig <= 0.0:
        sig = 0.15 * float(mttf)

    total_expected = 0.0
    clock_time = 0.0
    effective_age = float(current_age)
    buckets = [0.0] * num_buckets if num_buckets > 0 else []

    for _ in range(max_iterations):
        rem_clock = study_duration - clock_time
        if rem_clock <= 0:
            break

        age_at_lifecycle_end = effective_age + rem_clock

        if str(aging_distribution or "normal") == "weibull_2p":
            f_current = _weibull_cdf(effective_age, mttf=mttf, beta=beta_jaar)
        elif str(aging_distribution or "normal") == "truncated_normal_0":
            f_current = _truncated_normal_0_cdf(effective_age, mttf=mttf, sigma=sig)
        else:
            f_current = float(normal_cdf(effective_age, mttf, sig))
        survival_at_age = 1.0 - f_current

        if survival_at_age < 1e-10:
            break

        p_fails_before_end = _conditional_failures_with_rev_segments(
            effective_age,
            clock_start=clock_time,
            rem_clock=rem_clock,
            mttf=mttf,
            sigma=sig,
            aging_distribution=aging_distribution,
            beta_jaar=beta_jaar,
            rev_schedule=rev_schedule,
        )

        if p_fails_before_end < 1e-10:
            break

        total_expected += p_fails_before_end

        if num_buckets > 0:
            a0 = float(effective_age)
            a1 = float(age_at_lifecycle_end)
            if str(aging_distribution or "normal") == "weibull_2p":
                f_end = _weibull_cdf(a1, mttf=mttf, beta=beta_jaar)
            elif str(aging_distribution or "normal") == "truncated_normal_0":
                f_end = _truncated_normal_0_cdf(a1, mttf=mttf, sigma=sig)
            else:
                f_end = float(normal_cdf(a1, mttf, sig))
            denom = f_end - f_current
            cal_window_lo = float(clock_time)
            cal_window_hi = float(clock_time) + rem_clock
            if denom > 1e-18:
                slices = [0.0] * num_buckets
                for h in range(num_buckets):
                    bucket_cal_lo = float(h)
                    bucket_cal_hi = min(float(h) + 1.0, study_duration)
                    if bucket_cal_hi <= bucket_cal_lo:
                        continue
                    t0 = max(cal_window_lo, bucket_cal_lo)
                    t1 = min(cal_window_hi, bucket_cal_hi)
                    if t1 <= t0:
                        continue
                    age_lo = effective_age + (t0 - clock_time)
                    age_hi = effective_age + (t1 - clock_time)
                    age_lo = max(a0, age_lo)
                    age_hi = min(a1, age_hi)
                    if age_hi > age_lo:
                        if str(aging_distribution or "normal") == "weibull_2p":
                            phi_lo = _weibull_cdf(age_lo, mttf=mttf, beta=beta_jaar)
                            phi_hi = _weibull_cdf(age_hi, mttf=mttf, beta=beta_jaar)
                        elif str(aging_distribution or "normal") == "truncated_normal_0":
                            phi_lo = _truncated_normal_0_cdf(age_lo, mttf=mttf, sigma=sig)
                            phi_hi = _truncated_normal_0_cdf(age_hi, mttf=mttf, sigma=sig)
                        else:
                            phi_lo = float(normal_cdf(age_lo, mttf, sig))
                            phi_hi = float(normal_cdf(age_hi, mttf, sig))
                        slices[h] = max(0.0, phi_hi - phi_lo)
                tail = max(0.0, denom - float(sum(slices)))
                if tail > 1e-18:
                    last_h = -1
                    for h in range(num_buckets):
                        if float(h) < study_duration - 1e-12:
                            last_h = h
                    if last_h >= 0:
                        slices[last_h] += tail
                    else:
                        slices[0] += tail
                s_sum2 = float(sum(slices))
                if s_sum2 <= 1e-18:
                    buckets[0] += p_fails_before_end
                else:
                    for h in range(num_buckets):
                        buckets[h] += p_fails_before_end * (slices[h] / denom)
            else:
                buckets[0] += p_fails_before_end

        if str(aging_distribution or "normal") == "weibull_2p":
            f_lo = _weibull_cdf(effective_age, mttf=mttf, beta=beta_jaar)
            f_hi = _weibull_cdf(age_at_lifecycle_end, mttf=mttf, beta=beta_jaar)
            p_mid = min(1.0 - 1e-12, max(0.0, 0.5 * (f_lo + f_hi)))
            eta = _weibull_eta_from_mttf_beta(mttf, beta_jaar)
            expected_failure_age = float(eta * ((-math.log(1.0 - p_mid)) ** (1.0 / float(beta_jaar))))
        else:
            expected_failure_age = truncated_normal_conditional_mean(
                effective_age, age_at_lifecycle_end, mttf, sig
            )
        time_to_failure = expected_failure_age - effective_age
        clock_time += time_to_failure
        effective_age = rejuvenate_age(expected_failure_age, repair_quality)

    return total_expected, buckets


# ---------------------------------------------------------------------------
# AC-50 kalenderbuckets (slice 27)
# ---------------------------------------------------------------------------


def first_failure_mass_per_calendar_bucket(
    *,
    current_age: float,
    lifecycle_years: float,
    mttf: float,
    sigma: float,
) -> list[float]:
    """Phi-massa per kalenderbucket [age+h, age+h+1) voor eerste-faling (normaal)."""
    import math

    import numpy as np

    from rcm_core.normal_fast import bucket_phi_segments

    n = max(1, int(math.ceil(lifecycle_years)))
    edges = np.linspace(float(current_age), float(current_age) + n, n + 1)
    return bucket_phi_segments(edges, mttf, sigma).tolist()


def ac50_mass_fraction_strictly_after_mttf(
    masses: list[float],
    *,
    mttf_jaar: float,
) -> float:
    """Fractie van eerste-faling-massa in buckets die starten op of na ``mttf_jaar``."""
    total = float(sum(masses))
    if total <= 0.0:
        return 0.0
    start_idx = max(0, min(len(masses), int(mttf_jaar)))
    return float(sum(masses[start_idx:])) / total
