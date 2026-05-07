"""
distributions.py — Verdelingswiskunde voor faalkansberekeningen.

Alle functies zijn pure wiskunde: geen I/O, geen modelobjecten.
lru_cache voorkomt herberekening bij identieke parameters (veel FM's delen MTTF/sigma).

Tijdseenheden: jaren (leeftijden, MTTF, lifecycle). Uren alleen in conversies elders.
"""
from __future__ import annotations
import math
from functools import lru_cache

import numpy as np
from scipy import stats
from scipy import integrate


# ---------------------------------------------------------------------------
# Faalkansberekeningen
# ---------------------------------------------------------------------------

@lru_cache(maxsize=2048)
def p_failure_by_age(
    t: float,
    failure_type: str,
    mttf: float,
    sigma: float,
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
        if sigma <= 0:
            return 0.0
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

    # aging: numerieke integratie
    return _expected_failures_aging(current_age, lifecycle_years, mttf, sigma, repair_quality)


def _expected_failures_aging(
    current_age: float,
    lifecycle_end: float,
    mttf: float,
    sigma: float,
    repair_quality: float,
    max_iterations: int = 100,
) -> float:
    """Verwacht aantal falingen voor aging faalwijze via iteratieve integratie.

    Correcte aanpak: twee klokken bijhouden:
    - clock_time: verstreken kalendertijd (start = 0)
    - effective_age: effectieve leeftijd van het component op dat moment

    Na iedere faling:
    - clock_time += (failure_age - effective_age_before_failure)
    - effective_age = effective_age_after_repair(failure_age, repair_quality)
    """
    if sigma <= 0:
        sigma = 0.15 * mttf

    total_expected = 0.0
    clock_time = 0.0        # kalendertijd verstreken t.o.v. modeljaar
    effective_age = current_age

    for _ in range(max_iterations):
        remaining = lifecycle_end - clock_time
        if remaining <= 0:
            break

        # Age van het component als de lifecycle zou eindigen (zonder tussentijds falen)
        age_at_lifecycle_end = effective_age + remaining

        # P(faling | component heeft leeftijd effective_age, lifecycle stopt op age_at_lifecycle_end)
        # = P(T <= age_at_lifecycle_end | T > effective_age)
        f_current = stats.norm.cdf(effective_age, loc=mttf, scale=sigma)
        f_end = stats.norm.cdf(age_at_lifecycle_end, loc=mttf, scale=sigma)
        survival_at_age = 1.0 - f_current

        if survival_at_age < 1e-10:
            break

        p_fails_before_end = (f_end - f_current) / survival_at_age

        if p_fails_before_end < 1e-10:
            break

        total_expected += p_fails_before_end

        # Verwachte leeftijd bij falen (conditioneel): E[T | effective_age < T <= age_at_lifecycle_end]
        expected_failure_age = _conditional_mean_failure_age(
            effective_age, age_at_lifecycle_end, mttf, sigma
        )

        # Verstreken kalendertijd bij deze faling
        time_to_failure = expected_failure_age - effective_age
        clock_time += time_to_failure

        # Nieuwe effectieve leeftijd na reparatie
        effective_age = effective_age_after_repair(expected_failure_age, repair_quality)

    return total_expected


def _conditional_mean_failure_age(
    age_lower: float,
    age_upper: float,
    mttf: float,
    sigma: float,
) -> float:
    """Verwachte faalmomentsleeftijd gegeven dat falen optreedt tussen age_lower en age_upper."""
    # E[T | age_lower < T <= age_upper] = integral(t * f(t), lower, upper) / P(lower < T <= upper)
    f_lower = stats.norm.cdf(age_lower, loc=mttf, scale=sigma)
    f_upper = stats.norm.cdf(age_upper, loc=mttf, scale=sigma)
    p_interval = f_upper - f_lower

    if p_interval < 1e-12:
        return (age_lower + age_upper) / 2.0

    def integrand(t: float) -> float:
        return t * stats.norm.pdf(t, loc=mttf, scale=sigma)

    result, _ = integrate.quad(integrand, age_lower, age_upper, limit=50)
    return result / p_interval


# ---------------------------------------------------------------------------
# Monte Carlo sampling
# ---------------------------------------------------------------------------

def sample_time_to_failure(
    current_age: float,
    failure_type: str,
    mttf: float,
    sigma: float,
    rng: np.random.Generator,
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
        if sigma <= 0:
            sigma = 0.15 * mttf
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
