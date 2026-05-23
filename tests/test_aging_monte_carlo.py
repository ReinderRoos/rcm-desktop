"""Monte Carlo cross-check voor aging kalenderbuckets (slice 24 issue 08)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.distributions import (
    RevSchedule,
    _conditional_failures_with_rev_segments,
    build_rev_schedule,
    expected_aging_lifecycle_faalmomenten_ssot,
    rejuvenate_age,
)
from rcm_core.models import PMTask, TaskType
from rcm_core.normal_fast import normal_cdf, truncated_normal_conditional_mean


def _slice_weights_for_iteration(
    *,
    effective_age: float,
    age_at_lifecycle_end: float,
    clock_time: float,
    rem_clock: float,
    study_duration: float,
    mttf: float,
    sig: float,
    num_buckets: int,
) -> list[float]:
    f_current = float(normal_cdf(effective_age, mttf, sig))
    f_end = float(normal_cdf(age_at_lifecycle_end, mttf, sig))
    denom = f_end - f_current
    cal_window_lo = float(clock_time)
    cal_window_hi = float(clock_time) + rem_clock
    slices = [0.0] * num_buckets
    if denom > 1e-18:
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
            age_lo = max(float(effective_age), age_lo)
            age_hi = min(float(age_at_lifecycle_end), age_hi)
            if age_hi > age_lo:
                phi_lo = float(normal_cdf(age_lo, mttf, sig))
                phi_hi = float(normal_cdf(age_hi, mttf, sig))
                slices[h] = max(0.0, phi_hi - phi_lo)
        tail = max(0.0, denom - float(sum(slices)))
        if tail > 1e-18:
            last_h = max(
                (h for h in range(num_buckets) if float(h) < study_duration - 1e-12),
                default=0,
            )
            slices[last_h] += tail
    else:
        slices[0] = denom
    s_sum = float(sum(slices))
    if s_sum <= 1e-18:
        return [0.0] * num_buckets
    return [s / s_sum for s in slices]


def _monte_carlo_aging_buckets(
    *,
    current_age: float,
    lifecycle_years: float,
    mttf: float,
    sigma: float,
    repair_quality: float,
    num_buckets: int,
    rev_schedule: RevSchedule = (),
    n_paths: int = 15_000,
    seed: int = 42,
    max_iterations: int = 100,
) -> list[float]:
    rng = np.random.default_rng(seed)
    buckets = np.zeros(num_buckets, dtype=float)
    study_start_age = float(current_age)
    study_duration = float(lifecycle_years) - study_start_age
    if study_duration <= 0:
        return buckets.tolist()

    sig = float(sigma) if sigma > 0 else 0.15 * float(mttf)

    for _ in range(n_paths):
        clock_time = 0.0
        effective_age = study_start_age
        for _iter in range(max_iterations):
            rem_clock = study_duration - clock_time
            if rem_clock <= 0:
                break

            age_at_lifecycle_end = effective_age + rem_clock

            p_fail = _conditional_failures_with_rev_segments(
                effective_age,
                clock_start=clock_time,
                rem_clock=rem_clock,
                mttf=mttf,
                sigma=sig,
                rev_schedule=rev_schedule,
            )
            if p_fail < 1e-10:
                break

            weights = _slice_weights_for_iteration(
                effective_age=effective_age,
                age_at_lifecycle_end=age_at_lifecycle_end,
                clock_time=clock_time,
                rem_clock=rem_clock,
                study_duration=study_duration,
                mttf=mttf,
                sig=sig,
                num_buckets=num_buckets,
            )
            mass = [p_fail * w for w in weights]
            total_mass = float(sum(mass))
            if total_mass > 1e-12 and rng.random() < min(1.0, total_mass):
                probs = np.array(mass, dtype=float) / total_mass
                buckets[int(rng.choice(num_buckets, p=probs))] += 1.0

            expected_failure_age = truncated_normal_conditional_mean(
                effective_age, age_at_lifecycle_end, mttf, sig
            )
            time_to_failure = expected_failure_age - effective_age
            clock_time += time_to_failure
            effective_age = rejuvenate_age(expected_failure_age, repair_quality)

    return (buckets / n_paths).tolist()


def _assert_buckets_close(analytic: list[float], mc: list[float]) -> None:
    assert sum(mc) == pytest.approx(sum(analytic), rel=0.05, abs=0.05)
    for a, m in zip(analytic, mc, strict=True):
        if a < 0.01:
            continue
        rel = abs(a - m) / max(a, 1e-12)
        assert rel <= 0.05 or abs(a - m) <= 0.02


def test_aging_calendar_curve_matches_monte_carlo_without_rev():
    lifecycle = 60.0
    n_buckets = 60
    _, analytic = expected_aging_lifecycle_faalmomenten_ssot(
        current_age=0.0,
        lifecycle_years=lifecycle,
        mttf=20.0,
        sigma=4.0,
        repair_quality=0.7,
        num_buckets=n_buckets,
    )
    mc = _monte_carlo_aging_buckets(
        current_age=0.0,
        lifecycle_years=lifecycle,
        mttf=20.0,
        sigma=4.0,
        repair_quality=0.7,
        num_buckets=n_buckets,
    )
    _assert_buckets_close(analytic, mc)


def test_aging_calendar_curve_matches_monte_carlo_with_rev():
    lifecycle = 60.0
    n_buckets = 60
    rev = build_rev_schedule(
        [
            PMTask(
                pm_id="REV-1",
                fm_id="FM-1",
                taak_type=TaskType.REV,
                interval_jaar=10.0,
                aging_effect_pct=100.0,
            )
        ]
    )
    _, analytic = expected_aging_lifecycle_faalmomenten_ssot(
        current_age=0.0,
        lifecycle_years=lifecycle,
        mttf=20.0,
        sigma=4.0,
        repair_quality=0.7,
        num_buckets=n_buckets,
        rev_schedule=rev,
    )
    mc = _monte_carlo_aging_buckets(
        current_age=0.0,
        lifecycle_years=lifecycle,
        mttf=20.0,
        sigma=4.0,
        repair_quality=0.7,
        num_buckets=n_buckets,
        rev_schedule=rev,
    )
    _assert_buckets_close(analytic, mc)
