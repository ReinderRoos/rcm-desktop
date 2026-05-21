"""Tests voor rcm_core.normal_fast — snelle, gesloten-vorm normaalverdeling-helpers.

Deze module levert drie functies die in de motor en bucket-builders op hot paths
worden aangeroepen:

- ``normal_cdf(x, mu, sigma)``: numeriek gelijk aan ``scipy.stats.norm.cdf`` binnen 1e-12.
- ``truncated_normal_conditional_mean(a, b, mu, sigma)``: ``E[T | a < T <= b]`` via
  gesloten-vorm; numeriek gelijk aan ``scipy.integrate.quad``-resultaat binnen 1e-8.
- ``bucket_phi_segments(grenzen_array, mu, sigma)``: Φ-massa per bucket-interval in
  één vectorized call.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import integrate, stats

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestNormalCdfScalar:
    def test_normal_cdf_matches_scipy_within_1e_12(self) -> None:
        from rcm_core.normal_fast import normal_cdf

        mu = 20.0
        sigma = 4.0
        grid = np.linspace(mu - 5 * sigma, mu + 5 * sigma, 51)
        for x in grid:
            expected = float(stats.norm.cdf(float(x), loc=mu, scale=sigma))
            actual = float(normal_cdf(float(x), mu, sigma))
            assert abs(actual - expected) < 1e-12, (
                f"x={x}: actual={actual}, expected={expected}, diff={actual - expected}"
            )

    def test_normal_cdf_matches_scipy_for_various_mu_sigma(self) -> None:
        from rcm_core.normal_fast import normal_cdf

        cases = [(0.0, 1.0), (50.0, 7.5), (-10.0, 0.5), (100.0, 25.0)]
        for mu, sigma in cases:
            for x in [mu - 2 * sigma, mu - sigma, mu, mu + sigma, mu + 3 * sigma]:
                expected = float(stats.norm.cdf(x, loc=mu, scale=sigma))
                actual = float(normal_cdf(x, mu, sigma))
                assert abs(actual - expected) < 1e-12


class TestNormalCdfVectorized:
    def test_normal_cdf_accepts_numpy_array_and_matches_scipy(self) -> None:
        from rcm_core.normal_fast import normal_cdf

        mu = 20.0
        sigma = 4.0
        xs = np.linspace(mu - 4 * sigma, mu + 4 * sigma, 33)
        expected = stats.norm.cdf(xs, loc=mu, scale=sigma)
        actual = normal_cdf(xs, mu, sigma)
        assert isinstance(actual, np.ndarray)
        assert actual.shape == expected.shape
        np.testing.assert_allclose(actual, expected, atol=1e-12)

    def test_normal_cdf_scalar_input_returns_scalar_float(self) -> None:
        from rcm_core.normal_fast import normal_cdf

        result = normal_cdf(0.0, 0.0, 1.0)
        assert isinstance(result, float)
        assert abs(result - 0.5) < 1e-12


def _quad_conditional_mean(a: float, b: float, mu: float, sigma: float) -> float:
    """Referentie-implementatie via numerieke kwadratuur (zoals oude motor)."""
    f_a = stats.norm.cdf(a, loc=mu, scale=sigma)
    f_b = stats.norm.cdf(b, loc=mu, scale=sigma)
    p_interval = f_b - f_a
    if p_interval < 1e-12:
        return (a + b) / 2.0

    def integrand(t: float) -> float:
        return t * stats.norm.pdf(t, loc=mu, scale=sigma)

    result, _ = integrate.quad(integrand, a, b, limit=50)
    return result / p_interval


class TestTruncatedNormalConditionalMean:
    def test_truncated_conditional_mean_matches_quad_within_1e_8(self) -> None:
        from rcm_core.normal_fast import truncated_normal_conditional_mean

        mu = 20.0
        sigma = 4.0
        cases = [
            (mu - 2 * sigma, mu + 2 * sigma),
            (mu, mu + 2 * sigma),
            (mu - sigma, mu + sigma),
            (mu - 3 * sigma, mu),
            (mu - 4 * sigma, mu + 4 * sigma),
        ]
        for a, b in cases:
            expected = _quad_conditional_mean(a, b, mu, sigma)
            actual = truncated_normal_conditional_mean(a, b, mu, sigma)
            assert abs(actual - expected) < 1e-8, (
                f"a={a}, b={b}: actual={actual}, expected={expected}"
            )

    def test_truncated_conditional_mean_handles_empty_interval_returns_midpoint(
        self,
    ) -> None:
        from rcm_core.normal_fast import truncated_normal_conditional_mean

        mu = 20.0
        sigma = 4.0
        for a in [mu - 2 * sigma, mu, mu + 2 * sigma]:
            actual = truncated_normal_conditional_mean(a, a, mu, sigma)
            assert abs(actual - a) < 1e-12, f"a=b={a}: actual={actual}"

    def test_truncated_conditional_mean_reversed_interval_falls_back_to_midpoint(
        self,
    ) -> None:
        """``b < a`` is een defensieve invoer; geen exceptie, retourneer midpoint."""
        from rcm_core.normal_fast import truncated_normal_conditional_mean

        mu = 20.0
        sigma = 4.0
        actual = truncated_normal_conditional_mean(25.0, 22.0, mu, sigma)
        assert abs(actual - 23.5) < 1e-12

    def test_truncated_conditional_mean_far_tail_falls_back_to_midpoint(self) -> None:
        """In een uiterst klein tail-segment is ``p_interval`` numeriek nul; val terug."""
        from rcm_core.normal_fast import truncated_normal_conditional_mean

        mu = 20.0
        sigma = 4.0
        a, b = 80.0, 80.5
        actual = truncated_normal_conditional_mean(a, b, mu, sigma)
        assert abs(actual - 0.5 * (a + b)) < 1e-12


class TestSigmaGuards:
    def test_normal_cdf_with_zero_sigma_raises_value_error(self) -> None:
        from rcm_core.normal_fast import normal_cdf

        with pytest.raises(ValueError):
            normal_cdf(1.0, 0.0, 0.0)

    def test_normal_cdf_with_negative_sigma_raises_value_error(self) -> None:
        from rcm_core.normal_fast import normal_cdf

        with pytest.raises(ValueError):
            normal_cdf(1.0, 0.0, -2.0)

    def test_truncated_mean_with_zero_sigma_raises_value_error(self) -> None:
        from rcm_core.normal_fast import truncated_normal_conditional_mean

        with pytest.raises(ValueError):
            truncated_normal_conditional_mean(0.0, 1.0, 0.5, 0.0)

    def test_truncated_mean_with_negative_sigma_raises_value_error(self) -> None:
        from rcm_core.normal_fast import truncated_normal_conditional_mean

        with pytest.raises(ValueError):
            truncated_normal_conditional_mean(0.0, 1.0, 0.5, -1.0)

    def test_bucket_phi_segments_with_zero_sigma_raises_value_error(self) -> None:
        from rcm_core.normal_fast import bucket_phi_segments

        with pytest.raises(ValueError):
            bucket_phi_segments(np.array([0.0, 1.0, 2.0]), 0.5, 0.0)


class TestBucketPhiSegments:
    def test_bucket_phi_segments_matches_loop_within_1e_12(self) -> None:
        from rcm_core.normal_fast import bucket_phi_segments

        mu = 20.0
        sigma = 4.0
        edges = np.linspace(mu - 4 * sigma, mu + 4 * sigma, 51)
        expected = np.array(
            [
                float(stats.norm.cdf(edges[i + 1], loc=mu, scale=sigma))
                - float(stats.norm.cdf(edges[i], loc=mu, scale=sigma))
                for i in range(len(edges) - 1)
            ]
        )
        actual = bucket_phi_segments(edges, mu, sigma)
        assert isinstance(actual, np.ndarray)
        assert actual.shape == (len(edges) - 1,)
        np.testing.assert_allclose(actual, expected, atol=1e-12)

    def test_bucket_phi_segments_sums_to_total_phi_mass(self) -> None:
        """De som van segmenten over ``[edge_0, edge_n]`` is ``Phi(edge_n) - Phi(edge_0)``."""
        from rcm_core.normal_fast import bucket_phi_segments, normal_cdf

        mu = 20.0
        sigma = 4.0
        edges = np.array([0.0, 10.0, 20.0, 30.0, 50.0])
        segments = bucket_phi_segments(edges, mu, sigma)
        total = float(np.sum(segments))
        expected_total = normal_cdf(50.0, mu, sigma) - normal_cdf(0.0, mu, sigma)
        assert abs(total - expected_total) < 1e-12

    def test_bucket_phi_segments_handles_two_edges(self) -> None:
        from rcm_core.normal_fast import bucket_phi_segments

        mu = 20.0
        sigma = 4.0
        edges = np.array([10.0, 30.0])
        segments = bucket_phi_segments(edges, mu, sigma)
        assert segments.shape == (1,)
        expected = float(
            stats.norm.cdf(30.0, loc=mu, scale=sigma)
            - stats.norm.cdf(10.0, loc=mu, scale=sigma)
        )
        assert abs(float(segments[0]) - expected) < 1e-12
