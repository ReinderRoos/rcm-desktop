"""
fitting.py — MTTF en sigma fitten vanuit historische faaltijden.

Gebruikt het `reliability`-pakket (Matthew Reid) voor distribution fitting.
Valt terug op scipy als `reliability` niet beschikbaar is.

Ondersteunde verdelingen: normaal (aging), exponentieel (random).
Gecensureerde data (right-censored) wordt ondersteund via `censored_times`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class FitResult:
    """Resultaat van een distribution fit."""
    distribution: Literal["normal", "exponential"]
    mttf: float
    sigma: float          # 0.0 voor exponentieel
    goodness_of_fit: float  # log-likelihood of AIC (lager = beter)
    method: str           # "reliability" of "scipy"
    n_samples: int
    n_censored: int


def fit_from_failure_times(
    failure_times: list[float],
    censored_times: list[float] | None = None,
    distribution: Literal["normal", "exponential", "auto"] = "auto",
) -> FitResult:
    """Fit MTTF (en sigma) uit historische faaltijden.

    Parameters
    ----------
    failure_times : float-lijst in jaren (leeftijd bij falen)
    censored_times : right-censored observaties (component nog niet gefaald)
    distribution : welke verdeling te fitten; "auto" probeert beide en kiest beste AIC

    Returns
    -------
    FitResult met mttf, sigma, distribution, goodness_of_fit
    """
    if not failure_times:
        raise ValueError("failure_times mag niet leeg zijn")

    censored_times = censored_times or []

    try:
        return _fit_with_reliability(failure_times, censored_times, distribution)
    except ImportError:
        return _fit_with_scipy(failure_times, censored_times, distribution)


def _fit_with_reliability(
    failure_times: list[float],
    censored_times: list[float],
    distribution: str,
) -> FitResult:
    """Fit via het `reliability`-pakket."""
    from reliability.Fitters import Fit_Normal_2P, Fit_Expon_1P

    import numpy as np

    failures = np.array(failure_times, dtype=float)
    right_censored = np.array(censored_times, dtype=float) if censored_times else None

    results: list[FitResult] = []

    if distribution in ("normal", "auto"):
        fit = Fit_Normal_2P(
            failures=failures,
            right_censored=right_censored,
            print_results=False,
            show_probability_plot=False,
        )
        results.append(FitResult(
            distribution="normal",
            mttf=float(fit.mu),
            sigma=float(fit.sigma),
            goodness_of_fit=float(fit.AICc),
            method="reliability",
            n_samples=len(failure_times),
            n_censored=len(censored_times),
        ))

    if distribution in ("exponential", "auto"):
        fit = Fit_Expon_1P(
            failures=failures,
            right_censored=right_censored,
            print_results=False,
            show_probability_plot=False,
        )
        results.append(FitResult(
            distribution="exponential",
            mttf=float(1.0 / fit.Lambda),
            sigma=0.0,
            goodness_of_fit=float(fit.AICc),
            method="reliability",
            n_samples=len(failure_times),
            n_censored=len(censored_times),
        ))

    # Kies de fit met de laagste AICc (beste fit)
    return min(results, key=lambda r: r.goodness_of_fit)


def _fit_with_scipy(
    failure_times: list[float],
    censored_times: list[float],
    distribution: str,
) -> FitResult:
    """Fallback: fit via scipy (geen gecensureerde data support)."""
    import numpy as np
    from scipy import stats

    if censored_times:
        import warnings
        warnings.warn(
            "scipy-fallback ondersteunt geen gecensureerde data; censored_times worden genegeerd.",
            UserWarning,
            stacklevel=3,
        )

    data = np.array(failure_times, dtype=float)
    results: list[FitResult] = []

    if distribution in ("normal", "auto"):
        mu, sigma = stats.norm.fit(data)
        ll = float(stats.norm.logpdf(data, loc=mu, scale=sigma).sum())
        k = 2
        n = len(data)
        aic = 2 * k - 2 * ll
        aicc = aic + (2 * k * (k + 1)) / max(n - k - 1, 1)
        results.append(FitResult(
            distribution="normal",
            mttf=float(mu),
            sigma=float(sigma),
            goodness_of_fit=aicc,
            method="scipy",
            n_samples=n,
            n_censored=len(censored_times),
        ))

    if distribution in ("exponential", "auto"):
        loc, scale = stats.expon.fit(data, floc=0)
        ll = float(stats.expon.logpdf(data, loc=0, scale=scale).sum())
        k = 1
        n = len(data)
        aic = 2 * k - 2 * ll
        aicc = aic + (2 * k * (k + 1)) / max(n - k - 1, 1)
        results.append(FitResult(
            distribution="exponential",
            mttf=float(scale),
            sigma=0.0,
            goodness_of_fit=aicc,
            method="scipy",
            n_samples=n,
            n_censored=len(censored_times),
        ))

    return min(results, key=lambda r: r.goodness_of_fit)
