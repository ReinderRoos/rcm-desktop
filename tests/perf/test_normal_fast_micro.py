"""Micro-benchmarks voor de snelle normaalverdeling-helpers.

Deze tests zijn bewust klein genoeg om lokaal mee te draaien, maar groot genoeg
om regressies in de hot-path helpers zichtbaar te maken.
"""
from __future__ import annotations

import time
from collections.abc import Callable

import numpy as np
from scipy import integrate, stats

from rcm_core.normal_fast import (
    bucket_phi_segments,
    normal_cdf,
    truncated_normal_conditional_mean,
)


def _elapsed_seconds(action: Callable[[], None]) -> float:
    start = time.perf_counter()
    action()
    return time.perf_counter() - start


def _quad_conditional_mean(a: float, b: float, mu: float, sigma: float) -> float:
    f_a = stats.norm.cdf(a, loc=mu, scale=sigma)
    f_b = stats.norm.cdf(b, loc=mu, scale=sigma)
    p_interval = f_b - f_a
    if p_interval < 1e-12:
        return 0.5 * (a + b)

    def integrand(t: float) -> float:
        return t * stats.norm.pdf(t, loc=mu, scale=sigma)

    result, _ = integrate.quad(integrand, a, b, limit=50)
    return result / p_interval


def test_normal_cdf_scalar_is_at_least_30x_faster_than_scipy_stats() -> None:
    mu = 20.0
    sigma = 4.0
    xs = np.linspace(mu - 4 * sigma, mu + 4 * sigma, 20_000).tolist()

    scipy_seconds = _elapsed_seconds(
        lambda: [stats.norm.cdf(x, loc=mu, scale=sigma) for x in xs]
    )
    fast_seconds = _elapsed_seconds(lambda: [normal_cdf(x, mu, sigma) for x in xs])

    assert scipy_seconds / fast_seconds >= 30.0


def test_truncated_conditional_mean_is_at_least_20x_faster_than_quad() -> None:
    mu = 20.0
    sigma = 4.0
    a = mu - 2 * sigma
    b = mu + 2 * sigma
    iterations = 750

    quad_seconds = _elapsed_seconds(
        lambda: [_quad_conditional_mean(a, b, mu, sigma) for _ in range(iterations)]
    )
    fast_seconds = _elapsed_seconds(
        lambda: [
            truncated_normal_conditional_mean(a, b, mu, sigma)
            for _ in range(iterations)
        ]
    )

    assert quad_seconds / fast_seconds >= 20.0


def test_bucket_phi_segments_is_at_least_10x_faster_than_looped_scipy_cdf() -> None:
    mu = 20.0
    sigma = 4.0
    edges = np.linspace(0.0, 50.0, 51)
    iterations = 100

    loop_seconds = _elapsed_seconds(
        lambda: [
            [
                stats.norm.cdf(edges[i + 1], loc=mu, scale=sigma)
                - stats.norm.cdf(edges[i], loc=mu, scale=sigma)
                for i in range(len(edges) - 1)
            ]
            for _ in range(iterations)
        ]
    )
    fast_seconds = _elapsed_seconds(
        lambda: [bucket_phi_segments(edges, mu, sigma) for _ in range(iterations)]
    )

    assert loop_seconds / fast_seconds >= 10.0
