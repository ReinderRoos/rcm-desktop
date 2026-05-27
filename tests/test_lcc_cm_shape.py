"""Slice 42 issue 01 — LCC CM jaarprofiel vorm (D1)."""

from __future__ import annotations

import math

import pytest

from rcm_core.engine import run_analytical
from rcm_core.lcc_profile import ltap_horizon_bucket_count
from rcm_core.models import RCMProject

from rcm_desktop.adapter.horizon_bucket_series import motor_cor_eur_per_bucket
from tests.helpers.lcc_cm_shape import (
    aging_cm_share,
    characterize_cm_year_shape,
    coefficient_of_variation,
    max_mean_ratio,
    peak_bucket_index,
)


def test_coefficient_of_variation_on_flat_buckets_is_near_zero():
    buckets = (100.0, 100.0, 100.0, 100.0)
    assert coefficient_of_variation(buckets) < 0.01


def test_max_mean_ratio_detects_peaked_profile():
    buckets = (1.0, 1.0, 10.0, 1.0)
    assert max_mean_ratio(buckets) > 2.0


def test_aging_cm_share_counts_only_aging_failure_types():
    project = RCMProject.from_dict(
        {
            "config": {"lifecycle_years": 10.0, "modeljaar": 2026},
            "pbs_items": {},
            "functies": {},
            "faalwijzes": {
                "FM-A": {
                    "fm_id": "FM-A",
                    "pbs_id": "PBS-1",
                    "functie_id": "F1",
                    "faalwijze_omschrijving": "A",
                    "failure_type": "aging",
                    "mttf_jaar": 5.0,
                },
                "FM-R": {
                    "fm_id": "FM-R",
                    "pbs_id": "PBS-1",
                    "functie_id": "F1",
                    "faalwijze_omschrijving": "R",
                    "failure_type": "random",
                    "mttf_jaar": 5.0,
                },
            },
            "pm_tasks": {},
            "task_groups": {},
            "effect_klassen": {},
            "fm_effect_links": {},
            "pm_effect_links": {},
            "bibliotheek": {},
        }
    )
    from rcm_core.models import FMHorizonProfile, FMResult

    aging_result = FMResult(
        fm_id="FM-A",
        pbs_id="PBS-1",
        p_failure_lifecycle=0.0,
        expected_failures=0.0,
        expected_raw_downtime_hr=0.0,
        expected_detection_delay_hr=0.0,
        expected_total_downtime_hr=0.0,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=90.0,
        pm_cost_eur=0.0,
        total_cost_eur=90.0,
        risk_contribution=0.0,
        effect_bijdragen={},
        horizon_profile=FMHorizonProfile(cor_eur=[90.0], cor_downtime_hr=[0.0], hidden_nb_hr=[0.0]),
    )
    random_result = FMResult(
        fm_id="FM-R",
        pbs_id="PBS-1",
        p_failure_lifecycle=0.0,
        expected_failures=0.0,
        expected_raw_downtime_hr=0.0,
        expected_detection_delay_hr=0.0,
        expected_total_downtime_hr=0.0,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=10.0,
        pm_cost_eur=0.0,
        total_cost_eur=10.0,
        risk_contribution=0.0,
        effect_bijdragen={},
        horizon_profile=FMHorizonProfile(cor_eur=[10.0], cor_downtime_hr=[0.0], hidden_nb_hr=[0.0]),
    )
    assert aging_cm_share(project, [aging_result, random_result]) == pytest.approx(0.9)


def _single_fm_project(*, failure_type: str, mttf_jaar: float, lifecycle_years: float) -> RCMProject:
    sigma = round(0.15 * mttf_jaar, 1) if failure_type == "aging" else 0.0
    fm_fields: dict = {
        "fm_id": "FM-1",
        "pbs_id": "PBS-1",
        "functie_id": "F1",
        "faalwijze_omschrijving": "Synth",
        "failure_type": failure_type,
        "mttf_jaar": mttf_jaar,
        "sigma_jaar": sigma,
        "cost_cm_eur": 10_000.0,
        "downtime_per_failure": {"value": 1.0, "unit": "uur"},
    }
    return RCMProject.from_dict(
        {
            "config": {"lifecycle_years": lifecycle_years, "modeljaar": 2026},
            "pbs_items": {
                "PBS-1": {
                    "pbs_id": "PBS-1",
                    "object_naam": "O",
                    "element_naam": "E",
                    "bouwdeel_naam": "B",
                    "component_naam": "",
                    "multiplicity": 1,
                    "bouwjaar": 2026,
                },
            },
            "functies": {},
            "faalwijzes": {"FM-1": fm_fields},
            "pm_tasks": {},
            "task_groups": {},
            "effect_klassen": {},
            "fm_effect_links": {},
            "pm_effect_links": {},
            "bibliotheek": {},
        }
    )


def test_random_fm_yields_flat_cm_year_profile_via_run_analytical():
    project = _single_fm_project(failure_type="random", mttf_jaar=10.0, lifecycle_years=20.0)
    fm_results, _ = run_analytical(project, parallel=False)
    shape = characterize_cm_year_shape(project, fm_results)
    assert shape.reconciles
    assert shape.used_legacy is False
    assert shape.cv < 0.01
    assert shape.aging_cm_share == pytest.approx(0.0)


def test_aging_fm_yields_peaked_cm_year_profile_near_mttf():
    mttf = 20.0
    # Geen REV-taken: as-good-as-new zonder verjonging; studie lang genoeg voor één MTTF-piek.
    project = _single_fm_project(failure_type="aging", mttf_jaar=mttf, lifecycle_years=30.0)
    fm_results, _ = run_analytical(project, parallel=False)
    shape = characterize_cm_year_shape(project, fm_results)
    assert shape.reconciles
    assert shape.used_legacy is False
    assert shape.max_mean_ratio > 2.0
    assert shape.aging_cm_share == pytest.approx(1.0)
    peak_h = peak_bucket_index(shape.buckets)
    target_h = int(mttf) - 1
    assert abs(peak_h - target_h) <= 1


def test_fresh_run_uses_horizon_profile_cor_eur_not_legacy():
    project = _single_fm_project(failure_type="random", mttf_jaar=10.0, lifecycle_years=15.0)
    fm_results, _ = run_analytical(project, parallel=False)
    fmr = fm_results["FM-1"]
    assert fmr.horizon_profile is not None
    shape = characterize_cm_year_shape(project, fm_results)
    num = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    motor_buckets = motor_cor_eur_per_bucket(fmr, num)
    assert math.isclose(sum(motor_buckets), fmr.expected_cm_cost_eur, rel_tol=0, abs_tol=1e-3)
    assert sum(motor_buckets) > 0.0
    assert shape.used_legacy is False
