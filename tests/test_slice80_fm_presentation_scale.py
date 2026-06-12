"""Slice 80 issue 04 — gedeelde schaal-toggle schaalt FM-resultaten (Qt-vrij)."""

from __future__ import annotations

import pytest

from rcm_core.config import RCMConfig
from rcm_core.models import (
    FMHorizonProfile,
    FMResult,
    Faalwijze,
    PBSItem,
    RCMProject,
)
from rcm_core.units import TimeDuration, TimeUnit
from rcm_desktop.adapter.result_view_service import (
    apply_presentation_scale_to_fm_rows,
    build_rows,
)
from rcm_desktop.adapter.results_workspace_state import ContributionPresentation

NUM = 5


def _project() -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=float(NUM), modeljaar=2020),
        pbs_items={"PBS-1": PBSItem("PBS-1", "o", "e", "Pomp")},
        faalwijzes={
            "FM-1": Faalwijze(
                fm_id="FM-1",
                pbs_id="PBS-1",
                functie_id="F",
                faalwijze_omschrijving="Test",
                mttf_jaar=10.0,
                downtime_per_failure=TimeDuration(10.0, TimeUnit.HOURS),
            ),
        },
    )


def _fmr() -> FMResult:
    return FMResult(
        fm_id="FM-1",
        pbs_id="PBS-1",
        p_failure_lifecycle=0.5,
        expected_failures=10.0,
        expected_raw_downtime_hr=70.0,
        expected_detection_delay_hr=30.0,
        expected_total_downtime_hr=100.0,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=200.0,
        pm_cost_eur=50.0,
        total_cost_eur=250.0,
        risk_contribution=0.0,
        horizon_profile=FMHorizonProfile(
            cor_eur=[40.0, 40.0, 40.0, 40.0, 40.0],
            cor_downtime_hr=[14.0, 14.0, 14.0, 14.0, 14.0],
            hidden_nb_hr=[6.0, 6.0, 6.0, 6.0, 6.0],
        ),
    )


def test_lifecycle_presentation_keeps_motor_totals() -> None:
    project, fmr = _project(), _fmr()
    rows = build_rows(project, [fmr])
    pres = ContributionPresentation(horizon="lifecycle")
    out = apply_presentation_scale_to_fm_rows(
        project, fm_results=[fmr], rows=rows, presentation=pres, nb_filter=None
    )
    row = out[0]
    assert row.expected_failures == pytest.approx(10.0)
    assert row.expected_total_downtime_hr == pytest.approx(100.0)
    assert row.total_cost_eur == pytest.approx(250.0)


def test_per_year_average_scales_all_three_columns() -> None:
    project, fmr = _project(), _fmr()
    rows = build_rows(project, [fmr])
    lifecycle = apply_presentation_scale_to_fm_rows(
        project,
        fm_results=[fmr],
        rows=rows,
        presentation=ContributionPresentation(horizon="lifecycle"),
        nb_filter=None,
    )[0]
    per_year = apply_presentation_scale_to_fm_rows(
        project,
        fm_results=[fmr],
        rows=rows,
        presentation=ContributionPresentation(horizon="per_year", year_choice="average"),
        nb_filter=None,
    )[0]
    assert per_year.expected_total_downtime_hr == pytest.approx(
        lifecycle.expected_total_downtime_hr / NUM, rel=1e-6
    )
    assert per_year.total_cost_eur == pytest.approx(
        lifecycle.total_cost_eur / NUM, rel=1e-6
    )
