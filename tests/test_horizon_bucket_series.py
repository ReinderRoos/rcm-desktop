"""Tests — horizon bucket series public seam."""

from __future__ import annotations

from rcm_core.models import FMHorizonProfile, FMResult, RCMProject

from rcm_desktop.adapter.horizon_bucket_series import (
    faalmomenten_per_bucket,
    fm_horizon_context,
    motor_cor_eur_per_bucket,
)


def _minimal_project() -> RCMProject:
    return RCMProject.from_dict(
        {
            "config": {"lifecycle_years": 10.0, "modeljaar": 2026},
            "pbs_items": {
                "PBS-1": {
                    "pbs_id": "PBS-1",
                    "object_naam": "O",
                    "element_naam": "E",
                    "bouwdeel_naam": "B",
                    "component_naam": "",
                    "multiplicity": 1,
                    "bouwjaar": 2020,
                },
            },
            "functies": {},
            "faalwijzes": {
                "FM-1": {
                    "fm_id": "FM-1",
                    "pbs_id": "PBS-1",
                    "functie_id": "F1",
                    "faalwijze_omschrijving": "X",
                    "failure_type": "random",
                    "mttf_jaar": 5.0,
                    "downtime_per_failure": {"value": 1.0, "unit": "uur"},
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


def test_fm_horizon_context_uses_pbs_age_and_multiplicity():
    project = _minimal_project()
    age, lifecycle, mult = fm_horizon_context(project, "PBS-1")
    assert age == 6.0
    assert lifecycle == 16.0  # aw_mc_lifecycle_horizon=True: age + lifecycle_years
    assert mult == 1.0


def test_faalmomenten_per_bucket_returns_ten_buckets_for_random_fm():
    project = _minimal_project()
    fmr = FMResult(
        fm_id="FM-1",
        pbs_id="PBS-1",
        p_failure_lifecycle=0.5,
        expected_failures=2.0,
        expected_raw_downtime_hr=0.0,
        expected_detection_delay_hr=0.0,
        expected_total_downtime_hr=0.0,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=0.0,
        pm_cost_eur=0.0,
        total_cost_eur=0.0,
        risk_contribution=0.0,
        effect_bijdragen={},
    )
    buckets = faalmomenten_per_bucket(project, fmr)
    assert len(buckets) == 10
    assert sum(buckets) > 0.0


def test_motor_cor_eur_reads_horizon_profile():
    fmr = FMResult(
        fm_id="FM-1",
        pbs_id="PBS-1",
        p_failure_lifecycle=0.0,
        expected_failures=0.0,
        expected_raw_downtime_hr=0.0,
        expected_detection_delay_hr=0.0,
        expected_total_downtime_hr=0.0,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=100.0,
        pm_cost_eur=0.0,
        total_cost_eur=100.0,
        risk_contribution=0.0,
        effect_bijdragen={},
        horizon_profile=FMHorizonProfile(
            cor_eur=[10.0, 20.0],
            cor_downtime_hr=[0.0, 0.0],
            hidden_nb_hr=[0.0, 0.0],
        ),
    )
    assert motor_cor_eur_per_bucket(fmr, 3) == [10.0, 20.0, 0.0]
