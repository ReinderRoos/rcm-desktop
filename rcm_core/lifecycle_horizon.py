"""Studie-horizon t.o.v. AW LifeTime (ADR-0008 parity)."""

from __future__ import annotations


def effective_lifecycle_end_age(
    lifecycle_years: float,
    current_age: float,
    *,
    aw_mc_horizon: bool = False,
) -> float:
    """Absolute leeftijd-grens voor ``expected_failures_lifecycle``.

    - ``aw_mc_horizon=False`` (default): studie eindigt op ``lifecycle_years``
      (AW LifeTime als maximale leeftijd; resterend = L − huidige leeftijd).
    - ``aw_mc_horizon=True``: studie loopt ``lifecycle_years`` vooruit vanaf
      huidige leeftijd (AW Monte Carlo-semantiek).
    """
    if aw_mc_horizon:
        return float(current_age) + float(lifecycle_years)
    return float(lifecycle_years)


def study_duration_years(
    lifecycle_years: float,
    current_age: float,
    *,
    aw_mc_horizon: bool = False,
) -> float:
    """Effectieve studieduur in jaren voor één asset."""
    end = effective_lifecycle_end_age(
        lifecycle_years,
        current_age,
        aw_mc_horizon=aw_mc_horizon,
    )
    return max(0.0, end - float(current_age))
