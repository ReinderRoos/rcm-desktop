"""Kern: LCC-jaarbuckets — CM naar verwachte faalmomenten per horizonjaar (slice 21)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from rcm_core.engine import compute_fm_result
from rcm_core.lcc_profile import (
    build_cm_eur_per_bucket,
    expected_faalmomenten_per_bucket_proportional,
    expected_faalmomenten_per_bucket_random,
    ltap_horizon_bucket_count,
    overlap_years_per_bucket,
)
from rcm_core.models import RCMProject


@pytest.fixture
def sample_project() -> RCMProject:
    raw = json.loads(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def test_overlap_lengths_sum_to_study_span():
    current_age = 5.0
    lifecycle_end = 40.0
    num = ltap_horizon_bucket_count(40.0)
    assert num == 40
    ovs = overlap_years_per_bucket(current_age, lifecycle_end, num)
    assert len(ovs) == num
    assert math.isclose(sum(ovs), lifecycle_end - current_age)


def test_random_faalmomenten_per_bucket_sum_matches_total_rate():
    current_age = 0.0
    lifecycle_end = 10.0
    mttf = 5.0
    mult = 2.0
    num = ltap_horizon_bucket_count(10.0)
    moments = expected_faalmomenten_per_bucket_random(
        current_age=current_age,
        lifecycle_end_age=lifecycle_end,
        mttf=mttf,
        multiplicity=mult,
        num_buckets=num,
    )
    expected_total = mult * (lifecycle_end - current_age) / mttf
    assert math.isclose(sum(moments), expected_total)


def test_proportional_split_matches_total_failures():
    overlaps = [1.0, 2.0, 0.5]
    total = 7.0
    parts = expected_faalmomenten_per_bucket_proportional(total_expected_failures=total, overlaps=overlaps)
    assert math.isclose(sum(parts), total)
    assert math.isclose(parts[1] / parts[0], 2.0)


def test_build_cm_eur_per_bucket_reconciles_with_engine(sample_project: RCMProject):
    """Som jaarlijks correctief (faalgebonden) EUR == som FMResult.expected_cm_cost_eur voor sample-fixture."""
    project = sample_project
    fm_results = []
    for fm in project.faalwijzes.values():
        pbs = project.pbs_items.get(fm.pbs_id)
        if pbs is None:
            continue
        fm_results.append(
            compute_fm_result(
                fm,
                pbs,
                list(project.pm_tasks.values()),
                project.task_groups,
                project.config,
                all_pbs=project.pbs_items,
            )
        )
    cm_buckets = build_cm_eur_per_bucket(project, fm_results)
    target = sum(r.expected_cm_cost_eur for r in fm_results)
    assert math.isclose(sum(cm_buckets), target, rel_tol=0, abs_tol=1e-5)
