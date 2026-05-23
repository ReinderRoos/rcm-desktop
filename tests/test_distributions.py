"""Kern: distributions — aging SSOT, random faalmodel, kalenderbuckets (slice 22/24)."""

from __future__ import annotations

import math

import pytest

from rcm_core.distributions import (
    effective_age_after_repair,
    expected_aging_lifecycle_faalmomenten_ssot,
    expected_failures_lifecycle,
    p_failure_by_age,
    sample_time_to_failure,
)


class TestAgingLifecycleFaalmomentenSsot:
    """Slice 22 fase 2: aging totaal + buckets uit één motorpad (Φ-segmenten)."""

    def test_total_matches_expected_failures_lifecycle(self):
        for ca, ly, mttf, sig, rq in [
            (0.0, 80.0, 50.0, 7.5, 1.0),
            (20.0, 80.0, 40.0, 6.0, 0.5),
            (5.0, 60.0, 30.0, 0.0, 1.0),
        ]:
            legacy = expected_failures_lifecycle(ca, ly, "aging", mttf, sig, rq)
            total, _ = expected_aging_lifecycle_faalmomenten_ssot(
                current_age=ca,
                lifecycle_years=ly,
                mttf=mttf,
                sigma=sig,
                repair_quality=rq,
                num_buckets=0,
            )
            assert math.isclose(legacy, total, rel_tol=0.0, abs_tol=1e-9)

    def test_bucket_sum_equals_total(self):
        total, buckets = expected_aging_lifecycle_faalmomenten_ssot(
            current_age=0.0,
            lifecycle_years=80.0,
            mttf=50.0,
            sigma=7.5,
            repair_quality=1.0,
            num_buckets=80,
        )
        assert abs(sum(buckets) - total) < 1e-8

    def test_mass_concentrated_near_mttf_not_uniform(self):
        num = 80
        total, moments = expected_aging_lifecycle_faalmomenten_ssot(
            current_age=0.0,
            lifecycle_years=80.0,
            mttf=50.0,
            sigma=7.5,
            repair_quality=1.0,
            num_buckets=num,
        )
        assert total > 0.5
        i_max = max(range(num), key=lambda i: moments[i])
        assert 44 <= i_max <= 55
        assert max(moments) > 3.0 * (total / num)

    def test_not_uniform_fallback_smear(self):
        """Regressie: geen total/num_buckets gladstrijking."""
        num = 80
        total, buckets = expected_aging_lifecycle_faalmomenten_ssot(
            current_age=0.0,
            lifecycle_years=80.0,
            mttf=50.0,
            sigma=7.5,
            repair_quality=1.0,
            num_buckets=num,
        )
        assert total > 0.0
        uniform = total / num
        assert max(buckets) > 3.0 * uniform
        assert math.isclose(sum(buckets), total, abs_tol=1e-9)


def _local_peak_indices(values: list[float], *, min_frac_of_max: float = 0.08) -> list[int]:
    if not values:
        return []
    peak_val = max(values)
    if peak_val <= 0.0:
        return []
    thresh = peak_val * min_frac_of_max
    peaks: list[int] = []
    for i, v in enumerate(values):
        if v < thresh:
            continue
        left = values[i - 1] if i > 0 else 0.0
        right = values[i + 1] if i + 1 < len(values) else 0.0
        if v >= left and v >= right:
            peaks.append(i)
    return peaks


def _nearest_peak_to(target_h: int, peaks: list[int], *, tolerance: int = 1) -> bool:
    return any(abs(p - target_h) <= tolerance for p in peaks)


class TestAgingCalendarBuckets:
    """Slice 24 issue 02: kalender-correcte aging-bucket-mapping."""

    def test_aging_rq_one_periodic_peaks(self):
        mttf = 20.0
        lifecycle = 3.0 * mttf
        n = int(lifecycle)
        _, buckets = expected_aging_lifecycle_faalmomenten_ssot(
            current_age=0.0,
            lifecycle_years=lifecycle,
            mttf=mttf,
            sigma=4.0,
            repair_quality=1.0,
            num_buckets=n,
        )
        peaks = _local_peak_indices(buckets)
        assert len(peaks) >= 3
        for target in (int(mttf) - 1, int(2 * mttf) - 1, int(3 * mttf) - 1):
            assert _nearest_peak_to(target, peaks, tolerance=1), (
                f"geen piek bij kalenderjaar ~{target + 1}, peaks={peaks}"
            )

    def test_aging_no_repair_quality_one_peak(self):
        mttf = 20.0
        n = 25
        _, buckets = expected_aging_lifecycle_faalmomenten_ssot(
            current_age=0.0,
            lifecycle_years=float(n),
            mttf=mttf,
            sigma=4.0,
            repair_quality=0.0,
            num_buckets=n,
        )
        i_mttf = int(mttf) - 1
        assert buckets[i_mttf] > buckets[0] * 2.0
        assert max(buckets) > 3.0 * (sum(buckets) / n)

    def test_aging_rq_zero_increasing_hazard(self):
        mttf = 20.0
        n = int(3 * mttf)
        _, buckets = expected_aging_lifecycle_faalmomenten_ssot(
            current_age=0.0,
            lifecycle_years=float(n),
            mttf=mttf,
            sigma=4.0,
            repair_quality=0.0,
            num_buckets=n,
        )
        mid = n // 2
        assert sum(buckets[mid:]) > sum(buckets[:mid]) * 1.5

    def test_total_expected_failures_reconciles(self):
        cases = [
            (0.0, 80.0, 50.0, 7.5, 1.0),
            (20.0, 80.0, 40.0, 6.0, 0.5),
            (5.0, 60.0, 30.0, 4.5, 0.0),
            (0.0, 60.0, 20.0, 4.0, 1.0),
        ]
        for ca, ly, mttf, sig, rq in cases:
            total, buckets = expected_aging_lifecycle_faalmomenten_ssot(
                current_age=ca,
                lifecycle_years=ly,
                mttf=mttf,
                sigma=sig,
                repair_quality=rq,
                num_buckets=int(ly - ca),
            )
            assert abs(sum(buckets) - total) < 1e-9

    def test_calendar_first_bucket_concentration_for_old_component(self):
        mttf = 20.0
        current_age = 28.0
        lifecycle = 50.0
        study_years = int(lifecycle - current_age)
        _, buckets = expected_aging_lifecycle_faalmomenten_ssot(
            current_age=current_age,
            lifecycle_years=lifecycle,
            mttf=mttf,
            sigma=3.0,
            repair_quality=0.0,
            num_buckets=study_years,
        )
        wrong_age_bucket = min(int(mttf) - 1, study_years - 1)
        assert buckets[0] > buckets[wrong_age_bucket]
        assert buckets[0] > 0.0


class TestExpectedFailuresLifecycle:
    def test_random_is_memoryless(self):
        assert expected_failures_lifecycle(0.0, 10.0, "random", 5.0, 0.0, 1.0) == pytest.approx(2.0)
        assert expected_failures_lifecycle(5.0, 10.0, "random", 5.0, 0.0, 1.0) == pytest.approx(1.0)


class TestEffectiveAgeAfterRepair:
    def test_as_good_as_new(self):
        assert effective_age_after_repair(10.0, 1.0) == pytest.approx(0.0)

    def test_as_good_as_old(self):
        assert effective_age_after_repair(10.0, 0.0) == pytest.approx(10.0)


class TestPFailureByAge:
    def test_random_cdf(self):
        assert p_failure_by_age(0.0, "random", 10.0, 0.0) == pytest.approx(0.0)
        assert 0.0 < p_failure_by_age(10.0, "random", 10.0, 0.0) < 1.0


class TestNoUniformFallbackInSource:
    def test_source_has_no_uniform_fallback(self):
        from pathlib import Path

        source = Path("rcm_core/distributions.py").read_text(encoding="utf-8")
        assert "uniforme fallback" not in source.lower()
        assert "[float(total) / n]" not in source


class TestSampleTimeToFailure:
    def test_random_sample_positive(self):
        import numpy as np

        rng = np.random.default_rng(0)
        t = sample_time_to_failure(0.0, "random", 5.0, 0.0, rng)
        assert t >= 0.0
