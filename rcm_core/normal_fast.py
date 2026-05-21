"""
normal_fast.py — Snelle, gesloten-vorm normaalverdeling-helpers.

Deze module is de wiskundige fundering voor slice 24 (motor-correctheid +
5x performance). Hij vervangt scalaire ``scipy.stats.norm.cdf``-calls en
``scipy.integrate.quad``-aanroepen in de motor en bucket-builders door:

- ``normal_cdf``: schaalt naar standaardnormaal en gebruikt ``scipy.special.ndtr``
  (vector-vriendelijke C-implementatie van Phi).
- ``truncated_normal_conditional_mean``: gesloten-vorm
  ``mu + sigma * (phi(alpha) - phi(beta)) / (Phi(beta) - Phi(alpha))``.
- ``bucket_phi_segments``: vectorized Phi-massa per opeenvolgend interval.

Geen Qt-imports, geen domein-modellen. Pure wiskunde.
"""
from __future__ import annotations

import math
from typing import Union

import numpy as np
from scipy.special import ndtr

ArrayLike = Union[float, np.ndarray]

_INV_SQRT_2PI = 1.0 / math.sqrt(2.0 * math.pi)


def normal_cdf(x: ArrayLike, mu: float, sigma: float) -> ArrayLike:
    """``P(T <= x)`` voor T ~ Normaal(mu, sigma).

    Gebruikt ``scipy.special.ndtr`` op de gestandaardiseerde variabele zodat
    de call O(1) is en de Python-overhead van ``scipy.stats.norm.cdf``
    (object-dispatch via ``rv_frozen``) wordt vermeden.

    Polymorf: bij scalaire ``x`` retourneert het een ``float``, bij een numpy
    array een gelijkvormige ``ndarray``.

    Raises ``ValueError`` als ``sigma <= 0``. De aanroeper is verantwoordelijk
    voor een eventuele domein-specifieke fallback (de aging-engine substitueert
    bijvoorbeeld ``0.15 * mttf``).
    """
    if sigma <= 0.0:
        raise ValueError(f"sigma moet > 0 zijn, kreeg {sigma}")
    z = (x - mu) / sigma
    if isinstance(z, np.ndarray):
        return ndtr(z)
    return float(ndtr(z))


def _standard_normal_pdf(z: float) -> float:
    """Phi'(z) = (1/sqrt(2*pi)) * exp(-z^2/2). Sneller dan ``scipy.stats.norm.pdf``."""
    return _INV_SQRT_2PI * math.exp(-0.5 * z * z)


def truncated_normal_conditional_mean(
    a: float, b: float, mu: float, sigma: float
) -> float:
    """``E[T | a < T <= b]`` voor T ~ Normaal(mu, sigma), gesloten-vorm.

    Identiteit::

        E[T | a < T <= b] = mu + sigma * (phi(alpha) - phi(beta))
                                       / (Phi(beta) - Phi(alpha))

    met ``alpha = (a-mu)/sigma`` en ``beta = (b-mu)/sigma``. Dit vervangt
    de numerieke kwadratuur (`scipy.integrate.quad`) die in de oude motor
    per iteratie werd aangeroepen.

    Raises ``ValueError`` als ``sigma <= 0``. Defensieve fallback voor een
    numeriek leeg interval (``a == b`` of ``b < a`` of extreem ver in de
    staart) is het midpoint ``(a + b) / 2``; dit volgt de bestaande
    motor-conventie in ``rcm_core.distributions``.
    """
    if sigma <= 0.0:
        raise ValueError(f"sigma moet > 0 zijn, kreeg {sigma}")
    alpha = (a - mu) / sigma
    beta = (b - mu) / sigma
    p_interval = float(ndtr(beta) - ndtr(alpha))
    if p_interval < 1e-12:
        return 0.5 * (a + b)
    phi_alpha = _standard_normal_pdf(alpha)
    phi_beta = _standard_normal_pdf(beta)
    return mu + sigma * (phi_alpha - phi_beta) / p_interval


def bucket_phi_segments(edges: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """Phi-massa per opeenvolgend bucket-interval, vectorized.

    Voor ``edges`` met lengte ``n+1`` retourneert deze functie een array van
    lengte ``n`` waar element ``i`` gelijk is aan
    ``Phi(edges[i+1]) - Phi(edges[i])`` (met ``Phi`` de CDF van de
    Normaal(mu, sigma)-verdeling).

    Vervangt een Python-loop met ``stats.norm.cdf``-calls per bucket; de
    enige call is een vectorized ``ndtr``-evaluatie op ``edges``.
    """
    if sigma <= 0.0:
        raise ValueError(f"sigma moet > 0 zijn, kreeg {sigma}")
    z = (np.asarray(edges, dtype=float) - mu) / sigma
    phi_at_edges = ndtr(z)
    return np.diff(phi_at_edges)
