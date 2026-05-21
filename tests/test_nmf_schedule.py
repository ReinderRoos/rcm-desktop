"""Slice 27 — NMF-jaarpad (nmf_schedule) en horizonprofiel."""
from __future__ import annotations

import math

import pytest

from rcm_core.config import RCMConfig
from rcm_core.distributions import rejuvenate_age
from rcm_core.engine import compute_fm_result
from rcm_core.models import (
    FailureType,
    Faalwijze,
    PBSItem,
    PMTask,
    TaskType,
)
from rcm_core.nmf_schedule import (
    age_after_nmf_discovery,
    build_horizon_profile,
    next_test_time_years,
)
from rcm_core.units import TimeDuration, TimeUnit


def test_union_grid_earliest_test_wins():
    t = next_test_time_years(3.2, [5.0, 2.0])
    assert t == pytest.approx(4.0)


def test_nmf_hidden_nb_spread_over_overlap_years():
    moments = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    _, _, hidden = build_horizon_profile(
        faalmomenten=moments,
        is_evident=False,
        test_intervals_years=[5.0],
        cost_per_failure_eur=1000.0,
        downtime_per_failure_hr=100.0,
        num_buckets=7,
    )
    assert hidden[3] > 0.0
    assert hidden[4] > 0.0
    assert hidden[5] == pytest.approx(0.0, abs=1e-9)
    assert hidden[3] + hidden[4] == pytest.approx(100.0, rel=1e-6)


def test_nmf_cor_in_discovery_year_not_failure_year():
    moments = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    cor, cor_dt, _ = build_horizon_profile(
        faalmomenten=moments,
        is_evident=False,
        test_intervals_years=[2.0],
        cost_per_failure_eur=500.0,
        downtime_per_failure_hr=24.0,
        num_buckets=6,
    )
    assert cor[3] == pytest.approx(0.0, abs=1e-9)
    assert cor[4] == pytest.approx(500.0, rel=1e-6)
    assert cor_dt[4] == pytest.approx(24.0, rel=1e-6)


def test_evident_hidden_nb_zero():
    moments = [0.0, 2.0, 1.0]
    _, _, hidden = build_horizon_profile(
        faalmomenten=moments,
        is_evident=True,
        test_intervals_years=[1.0],
        cost_per_failure_eur=1.0,
        downtime_per_failure_hr=1.0,
        num_buckets=3,
    )
    assert sum(hidden) == pytest.approx(0.0, abs=1e-12)


def test_aging_repair_quality_after_nmf_discovery():
    age = age_after_nmf_discovery(
        study_start_age=0.0,
        discovery_study_year=5.0,
        repair_quality=0.3,
    )
    assert age == pytest.approx(rejuvenate_age(5.0, 0.3), rel=1e-9)


@pytest.fixture
def config():
    return RCMConfig(lifecycle_years=10.0, modeljaar=2026)


@pytest.fixture
def pbs():
    return PBSItem("PBS-1", "O", "E", "B", bouwjaar=2026, ontwerpleeftijd_jaar=40.0)


def test_fm_result_horizon_profile_reconciles(config, pbs):
    fm = Faalwijze(
        "FM-1", pbs.pbs_id, "F-1", "hidden",
        failure_type=FailureType.RANDOM,
        mttf_jaar=5.0,
        is_evident=False,
        cost_cm_eur=1000.0,
        downtime_per_failure=TimeDuration(10.0, TimeUnit.HOURS),
    )
    pm = PMTask(
        "PM-TST", "FM-1", TaskType.TST,
        interval_jaar=2.0,
        duration=TimeDuration(1.0, TimeUnit.HOURS),
        cost_eur=50.0,
    )
    result = compute_fm_result(fm, pbs, [pm], {}, config)
    assert result.horizon_profile is not None
    hp = result.horizon_profile
    assert sum(hp.hidden_nb_hr) == pytest.approx(
        result.expected_detection_delay_hr, rel=1e-6, abs=1e-6
    )
    assert sum(hp.cor_eur) == pytest.approx(result.expected_cm_cost_eur, rel=1e-6, abs=1e-3)
