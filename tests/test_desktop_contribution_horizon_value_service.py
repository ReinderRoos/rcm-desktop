from __future__ import annotations

import math

from rcm_core.config import RCMConfig
from rcm_core.models import FMHorizonProfile, FMResult, Faalwijze, PBSItem, RCMProject
from rcm_desktop.adapter.contribution_horizon_value_service import (
    contribution_value_for_fm,
)
from rcm_desktop.adapter.results_workspace_state import ContributionPresentation


def _project_with_horizon(num_buckets: int = 5) -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=float(num_buckets), modeljaar=2020),
        pbs_items={"PBS-1": PBSItem("PBS-1", "o", "e", "Pomp")},
        faalwijzes={
            "FM-1": Faalwijze(
                fm_id="FM-1",
                pbs_id="PBS-1",
                functie_id="F",
                faalwijze_omschrijving="Test",
                mttf_jaar=10.0,
            ),
        },
    )


def _fmr_with_profile(
    *,
    failures: float = 3.0,
    cor_dt: list[float] | None = None,
    hidden: list[float] | None = None,
    pm_dt: float = 2.0,
    cor_dt_total: float = 8.0,
) -> FMResult:
    num = 5
    cor_dt = cor_dt or [2.0, 2.0, 2.0, 1.0, 1.0]
    hidden = hidden or [0.0] * num
    return FMResult(
        fm_id="FM-1",
        pbs_id="PBS-1",
        p_failure_lifecycle=0.1,
        expected_failures=failures,
        expected_raw_downtime_hr=cor_dt_total - 0.5,
        expected_detection_delay_hr=0.5,
        expected_total_downtime_hr=cor_dt_total,
        expected_pm_downtime_hr=pm_dt,
        expected_cm_cost_eur=100.0,
        pm_cost_eur=50.0,
        total_cost_eur=150.0,
        risk_contribution=0.01,
        effect_bijdragen={},
        horizon_profile=FMHorizonProfile(
            cor_eur=[20.0] * num,
            cor_downtime_hr=cor_dt,
            hidden_nb_hr=hidden,
        ),
    )


def test_nb_lifecycle_percent_matches_legacy_formula():
    project = _project_with_horizon()
    fmr = _fmr_with_profile(cor_dt_total=10.0, pm_dt=5.0)
    pres = ContributionPresentation(
        horizon="lifecycle", unavailability_display="percent"
    )
    val = contribution_value_for_fm(
        project, fmr, metric="niet_beschikbaarheid", presentation=pres
    )
    lifecycle_h = 5 * 8760.0
    expected = (15.0 / lifecycle_h) * 100.0
    assert math.isclose(val, expected, rel_tol=0, abs_tol=1e-6)


def test_nb_lifecycle_hours_is_total_downtime():
    project = _project_with_horizon()
    fmr = _fmr_with_profile(cor_dt_total=10.0, pm_dt=5.0)
    pres = ContributionPresentation(
        horizon="lifecycle", unavailability_display="hours"
    )
    val = contribution_value_for_fm(
        project, fmr, metric="niet_beschikbaarheid", presentation=pres
    )
    assert math.isclose(val, 15.0, rel_tol=0, abs_tol=1e-3)


def test_nb_per_year_average_hours_is_mean_bucket():
    project = _project_with_horizon()
    fmr = _fmr_with_profile()
    pres = ContributionPresentation(
        horizon="per_year",
        year_choice="average",
        unavailability_display="hours",
    )
    val = contribution_value_for_fm(
        project, fmr, metric="niet_beschikbaarheid", presentation=pres
    )
    assert val > 0.0


def test_nb_specific_calendar_year_percent_uses_8760():
    project = _project_with_horizon()
    fmr = _fmr_with_profile(cor_dt=[10.0, 0.0, 0.0, 0.0, 0.0], pm_dt=0.0, cor_dt_total=10.0)
    pres = ContributionPresentation(
        horizon="per_year",
        year_choice=2020,
        unavailability_display="percent",
    )
    val = contribution_value_for_fm(
        project, fmr, metric="niet_beschikbaarheid", presentation=pres
    )
    expected = (10.0 / 8760.0) * 100.0
    assert math.isclose(val, expected, rel_tol=0, abs_tol=1e-4)


def test_faalmomenten_lifecycle_equals_expected_failures():
    project = _project_with_horizon()
    fmr = _fmr_with_profile(failures=4.5)
    pres = ContributionPresentation(horizon="lifecycle")
    val = contribution_value_for_fm(
        project, fmr, metric="faalmomenten", presentation=pres
    )
    assert math.isclose(val, 4.5, rel_tol=0, abs_tol=1e-6)
