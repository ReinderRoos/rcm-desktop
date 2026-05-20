from __future__ import annotations

import math

from rcm_core.config import RCMConfig
from rcm_core.models import FMHorizonProfile, FMResult, Faalwijze, PBSItem, RCMProject
from rcm_desktop.adapter.fm_verification_service import build_fm_verification_view


def _project_with_horizon(num_buckets: int = 5) -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=float(num_buckets), modeljaar=2020),
        pbs_items={"PBS-1": PBSItem("PBS-1", "o", "e", "Pomp")},
        faalwijzes={
            "FM-1": Faalwijze(
                fm_id="FM-1",
                pbs_id="PBS-1",
                functie_id="F",
                faalwijze_omschrijving="Test FM",
                mttf_jaar=10.0,
            ),
        },
    )


def _fmr_with_profile(
    *,
    failures: float = 3.0,
    cor_dt: list[float] | None = None,
    hidden: list[float] | None = None,
) -> FMResult:
    num = 5
    cor_dt = cor_dt or [2.0, 2.0, 2.0, 1.0, 1.0]
    hidden = hidden or [0.5, 0.0, 0.0, 0.0, 0.0]
    return FMResult(
        fm_id="FM-1",
        pbs_id="PBS-1",
        p_failure_lifecycle=0.1,
        expected_failures=failures,
        expected_raw_downtime_hr=7.5,
        expected_detection_delay_hr=0.5,
        expected_total_downtime_hr=8.0,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=100.0,
        pm_cost_eur=50.0,
        total_cost_eur=150.0,
        risk_contribution=0.01,
        effect_bijdragen={"EK-1": 1.5},
        horizon_profile=FMHorizonProfile(
            cor_eur=[20.0] * num,
            cor_downtime_hr=cor_dt,
            hidden_nb_hr=hidden,
        ),
    )


def test_build_fm_verification_view_without_profile_is_missing():
    project = _project_with_horizon()
    fmr = _fmr_with_profile()
    fmr = FMResult(
        fm_id=fmr.fm_id,
        pbs_id=fmr.pbs_id,
        p_failure_lifecycle=fmr.p_failure_lifecycle,
        expected_failures=fmr.expected_failures,
        expected_raw_downtime_hr=fmr.expected_raw_downtime_hr,
        expected_detection_delay_hr=fmr.expected_detection_delay_hr,
        expected_total_downtime_hr=fmr.expected_total_downtime_hr,
        expected_pm_downtime_hr=fmr.expected_pm_downtime_hr,
        expected_cm_cost_eur=fmr.expected_cm_cost_eur,
        pm_cost_eur=fmr.pm_cost_eur,
        total_cost_eur=fmr.total_cost_eur,
        risk_contribution=fmr.risk_contribution,
        effect_bijdragen=fmr.effect_bijdragen,
        horizon_profile=None,
    )
    view = build_fm_verification_view(project, fmr)
    assert view.profile_missing is True
    assert view.year_rows == ()
    assert view.reconcile_ok is False
    assert any("horizon_profile" in n for n in view.reconcile_notes)


def test_build_fm_verification_view_with_profile_has_calendar_year_rows():
    project = _project_with_horizon()
    fmr = _fmr_with_profile()
    view = build_fm_verification_view(project, fmr)
    assert not view.profile_missing
    assert len(view.year_rows) == 5
    assert view.year_rows[0].calendar_year == 2020
    assert view.year_rows[-1].calendar_year == 2024


def test_build_fm_verification_view_reconcile_warns_when_faalmomenten_proxy_differs():
    project = _project_with_horizon()
    fmr = _fmr_with_profile(failures=3.0)
    view = build_fm_verification_view(project, fmr)
    assert view.reconcile_ok is False
    assert any("Faalmomenten" in n for n in view.reconcile_notes)


def test_build_fm_verification_view_reconcile_ok_when_buckets_align():
    project = _project_with_horizon()
    fmr = _fmr_with_profile(failures=0.5)
    view = build_fm_verification_view(project, fmr)
    assert view.reconcile_ok is True
    assert any("OK" in n for n in view.reconcile_notes)


def test_build_fm_verification_view_returns_identity_and_lifecycle():
    project = _project_with_horizon()
    fmr = _fmr_with_profile()
    view = build_fm_verification_view(project, fmr)
    assert view.fm_id == "FM-1"
    assert view.faalwijze_omschrijving == "Test FM"
    assert view.pbs_id == "PBS-1"
    assert view.bouwdeel_naam == "Pomp"
    assert math.isclose(view.lifecycle.expected_failures, 3.0)
    assert math.isclose(view.lifecycle.total_cost_eur, 150.0)
    assert view.fm_input_hash is not None
    assert len(view.fm_input_hash) == 64
