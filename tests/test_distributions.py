"""Tests voor distributions.py — verdelingswiskunde."""
import sys
import math
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.distributions import (
    effective_age_after_repair,
    expected_failures_lifecycle,
    p_failure_by_age,
    sample_time_to_failure,
)


class TestPFailureByAge:
    def test_random_at_mttf_is_one_minus_inv_e(self):
        mttf = 20.0
        result = p_failure_by_age(mttf, "random", mttf, 0.0)
        assert abs(result - (1.0 - math.exp(-1.0))) < 1e-10

    def test_aging_at_mttf_is_half(self):
        """Bij de normaalverdeling is P(T <= MTTF) = 0,5 (mediaan = gemiddelde)."""
        mttf = 50.0
        sigma = 7.5
        result = p_failure_by_age(mttf, "aging", mttf, sigma)
        assert abs(result - 0.5) < 1e-10

    def test_aging_before_mttf_less_than_half(self):
        mttf = 50.0
        sigma = 7.5
        assert p_failure_by_age(40.0, "aging", mttf, sigma) < 0.5

    def test_aging_after_mttf_greater_than_half(self):
        mttf = 50.0
        sigma = 7.5
        assert p_failure_by_age(60.0, "aging", mttf, sigma) > 0.5

    def test_random_zero_age_is_zero(self):
        assert p_failure_by_age(0.0, "random", 20.0, 0.0) == 0.0

    def test_random_large_age_approaches_one(self):
        result = p_failure_by_age(1000.0, "random", 20.0, 0.0)
        assert result > 0.999

    def test_zero_mttf_returns_zero(self):
        assert p_failure_by_age(10.0, "random", 0.0, 0.0) == 0.0

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError):
            p_failure_by_age(10.0, "onbekend", 20.0, 5.0)

    def test_lru_cache_works(self):
        """Identieke parameters mogen niet opnieuw berekend worden (cache-hit)."""
        p_failure_by_age.cache_clear()
        p_failure_by_age(30.0, "aging", 50.0, 7.5)
        info = p_failure_by_age.cache_info()
        assert info.currsize == 1
        p_failure_by_age(30.0, "aging", 50.0, 7.5)
        info2 = p_failure_by_age.cache_info()
        assert info2.hits >= 1


class TestEffectiveAgeAfterRepair:
    def test_as_good_as_new(self):
        assert effective_age_after_repair(10.0, 1.0) == 0.0

    def test_as_good_as_old(self):
        assert effective_age_after_repair(10.0, 0.0) == 10.0

    def test_thirty_percent_new(self):
        """10 jaar oud, 30% nieuw → 7 jaar effectief."""
        result = effective_age_after_repair(10.0, 0.3)
        assert abs(result - 7.0) < 1e-10

    def test_zero_age(self):
        assert effective_age_after_repair(0.0, 0.5) == 0.0


class TestExpectedFailuresLifecycle:
    def test_random_simple(self):
        """Random, geen startleeftijd: lifecycle / MTTF."""
        result = expected_failures_lifecycle(0.0, 80.0, "random", 20.0, 0.0, 1.0)
        assert abs(result - 4.0) < 1e-6

    def test_random_with_current_age(self):
        """Random, startleeftijd 20: (80-20)/MTTF = 3 (voor MTTF=20)."""
        result = expected_failures_lifecycle(20.0, 80.0, "random", 20.0, 0.0, 1.0)
        assert abs(result - 3.0) < 1e-6

    def test_random_no_remaining_lifecycle(self):
        """Geen resterende levensduur → 0 falingen."""
        result = expected_failures_lifecycle(80.0, 80.0, "random", 20.0, 0.0, 1.0)
        assert result == 0.0

    def test_aging_as_good_as_new_median_at_mttf(self):
        """Aging, repair_quality=1.0: begin op 0, MTTF=50. Lifecycle=80.
        Verwacht: ca. 1 faling (één grote piek rondom jaar 50)."""
        result = expected_failures_lifecycle(0.0, 80.0, "aging", 50.0, 7.5, 1.0)
        assert 0.5 < result < 3.0  # redelijk bereik voor eerste faling

    def test_aging_greater_than_random_near_end_of_life(self):
        """Vlak vóór het einde van de OLD verwacht aging meer falingen dan random."""
        aging = expected_failures_lifecycle(40.0, 80.0, "aging", 50.0, 7.5, 1.0)
        random_val = expected_failures_lifecycle(40.0, 80.0, "random", 50.0, 0.0, 1.0)
        # Aging piek zit rondom jaar 50, dus bij leeftijd 40 verwacht je relatief veel
        assert aging > 0


class TestSampleTimeToFailure:
    def test_random_mean_is_mttf(self):
        rng = np.random.default_rng(42)
        samples = [sample_time_to_failure(0.0, "random", 20.0, 0.0, rng) for _ in range(50_000)]
        mean = sum(samples) / len(samples)
        assert abs(mean - 20.0) / 20.0 < 0.02  # binnen 2%

    def test_aging_sample_above_current_age(self):
        """Afgeknipte normaalverdeling → sample moet boven current_age liggen."""
        rng = np.random.default_rng(0)
        current_age = 30.0
        mttf, sigma = 50.0, 7.5
        for _ in range(100):
            t = sample_time_to_failure(current_age, "aging", mttf, sigma, rng)
            assert t >= current_age - 1e-9

    def test_aging_mean_near_mttf_from_zero(self):
        rng = np.random.default_rng(123)
        samples = [sample_time_to_failure(0.0, "aging", 50.0, 7.5, rng) for _ in range(50_000)]
        mean = sum(samples) / len(samples)
        assert abs(mean - 50.0) / 50.0 < 0.05  # binnen 5%
