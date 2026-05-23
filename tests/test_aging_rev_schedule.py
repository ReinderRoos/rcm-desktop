"""Slice 24 issue 04 — REV-verjonging in aging-motor."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.distributions import (
    apply_rev_along_calendar_segment,
    build_rev_schedule,
    expected_aging_lifecycle_faalmomenten_ssot,
    expected_failures_lifecycle,
    rejuvenate_age,
)
from rcm_core.models import PMTask, TaskType


def test_rev_task_reduces_expected_failures_compared_to_no_rev():
    base = expected_failures_lifecycle(0.0, 50.0, "aging", 20.0, 4.0, 1.0, rev_schedule=())
    with_rev = expected_failures_lifecycle(
        0.0,
        50.0,
        "aging",
        20.0,
        4.0,
        1.0,
        rev_schedule=((10.0, 1.0),),
    )
    assert with_rev < base * 0.95


def test_rejuvenate_age_matches_repair_quality_semantics():
    assert rejuvenate_age(18.0, 0.33) == pytest.approx(18.0 * (1.0 - 0.33))


def test_rev_multiplicative_when_multiple_simultaneous():
    age = 19.0
    age = apply_rev_along_calendar_segment(
        age,
        clock_start=9.0,
        clock_end=10.0,
        rev_schedule=((10.0, 0.5), (10.0, 0.5)),
    )
    assert age == pytest.approx(5.0)


def test_rev_shifts_bucket_curve_via_build_rev_schedule():
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
    _, without = expected_aging_lifecycle_faalmomenten_ssot(
        current_age=0.0,
        lifecycle_years=60.0,
        mttf=20.0,
        sigma=4.0,
        repair_quality=0.7,
        num_buckets=60,
    )
    _, with_rev = expected_aging_lifecycle_faalmomenten_ssot(
        current_age=0.0,
        lifecycle_years=60.0,
        mttf=20.0,
        sigma=4.0,
        repair_quality=0.7,
        num_buckets=60,
        rev_schedule=rev,
    )
    assert sum(with_rev) < sum(without) * 0.98
    assert sum(abs(a - b) for a, b in zip(without, with_rev, strict=True)) > 0.01
