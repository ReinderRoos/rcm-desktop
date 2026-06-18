"""Slice 101 issue 01 — MC FM presentation-scale helper (TDD, Qt-vrij)."""

from __future__ import annotations

import pytest

from rcm_core.config import RCMConfig
from rcm_core.effect_impact_service import EffectNbFilterSet
from rcm_core.models import Faalwijze, PBSItem, RCMProject
from rcm_core.simulation_engine import FMMCResult, MetricBand
from rcm_core.units import TimeDuration, TimeUnit
from rcm_desktop.adapter.result_view_service import (
    apply_presentation_scale_to_fm_rows,
    apply_presentation_scale_to_mc_rows,
    build_rows,
)
from rcm_desktop.adapter.results_workspace_state import ContributionPresentation
from rcm_desktop.adapter.simulation_engine_service import (
    FMMCResultRow,
    MCRunResult,
    fm_results_from_mc_p50,
)

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


def _mc_run(
    *,
    failures: MetricBand,
    downtime: MetricBand,
    cost: MetricBand,
) -> MCRunResult:
    row = FMMCResultRow(
        fm_id="FM-1",
        faalwijze_omschrijving="Test",
        bouwdeel_naam="Pomp",
        failures_band=failures,
        downtime_band=downtime,
        cost_band=cost,
        is_nmf=False,
        rf=0.0,
    )
    mc_fm = FMMCResult(
        fm_id="FM-1",
        pbs_id="PBS-1",
        failures=failures,
        downtime_hr=downtime,
        total_cost_eur=cost,
        n_completed=100,
        seed=1,
    )
    return MCRunResult(
        status="done",
        seed=1,
        n_completed=100,
        fm_results={"FM-1": mc_fm},
        rows=(row,),
    )


def test_lifecycle_presentation_keeps_display_p50_at_lifecycle_scalars() -> None:
    project = _project()
    failures = MetricBand(p10=8.0, p50=10.0, p90=12.0)
    downtime = MetricBand(p10=80.0, p50=100.0, p90=120.0)
    cost = MetricBand(p10=200.0, p50=250.0, p90=300.0)
    mc = _mc_run(failures=failures, downtime=downtime, cost=cost)
    pres = ContributionPresentation(horizon="lifecycle")

    out = apply_presentation_scale_to_mc_rows(
        project,
        mc,
        mc.rows,
        presentation=pres,
        nb_filter=None,
    )[0]

    assert out.failures_band.p50 == pytest.approx(10.0)
    assert out.cost_band.p50 == pytest.approx(250.0)
    assert out.failures_band.p10 == pytest.approx(8.0)
    assert out.failures_band.p90 == pytest.approx(12.0)


def test_per_year_average_matches_analytical_scale() -> None:
    project = _project()
    failures = MetricBand(p10=8.0, p50=10.0, p90=12.0)
    downtime = MetricBand(p10=80.0, p50=100.0, p90=120.0)
    cost = MetricBand(p10=200.0, p50=250.0, p90=300.0)
    mc = _mc_run(failures=failures, downtime=downtime, cost=cost)
    pres = ContributionPresentation(horizon="per_year", year_choice="average")
    fm_results = fm_results_from_mc_p50(project, mc)
    analytical = apply_presentation_scale_to_fm_rows(
        project,
        fm_results,
        build_rows(project, fm_results),
        presentation=pres,
        nb_filter=None,
    )[0]
    mc_scaled = apply_presentation_scale_to_mc_rows(
        project, mc, mc.rows, presentation=pres, nb_filter=None
    )[0]

    assert mc_scaled.failures_band.p50 == pytest.approx(analytical.expected_failures)
    assert mc_scaled.downtime_band.p50 == pytest.approx(
        analytical.expected_total_downtime_hr
    )
    assert mc_scaled.cost_band.p50 == pytest.approx(analytical.total_cost_eur)


def test_per_year_average_scales_p10_p90_proportionally() -> None:
    project = _project()
    failures = MetricBand(p10=8.0, p50=10.0, p90=12.0)
    mc = _mc_run(
        failures=failures,
        downtime=MetricBand(p10=80.0, p50=100.0, p90=120.0),
        cost=MetricBand(p10=200.0, p50=250.0, p90=300.0),
    )
    lifecycle_pres = ContributionPresentation(horizon="lifecycle")
    per_year_pres = ContributionPresentation(horizon="per_year", year_choice="average")

    lifecycle = apply_presentation_scale_to_mc_rows(
        project, mc, mc.rows, presentation=lifecycle_pres, nb_filter=None
    )[0]
    per_year = apply_presentation_scale_to_mc_rows(
        project, mc, mc.rows, presentation=per_year_pres, nb_filter=None
    )[0]

    ratio = per_year.failures_band.p50 / lifecycle.failures_band.p50
    assert per_year.failures_band.p10 == pytest.approx(lifecycle.failures_band.p10 * ratio)
    assert per_year.failures_band.p90 == pytest.approx(lifecycle.failures_band.p90 * ratio)


def test_specific_calendar_year_matches_analytical_scale() -> None:
    project = _project()
    failures = MetricBand(p10=8.0, p50=10.0, p90=12.0)
    downtime = MetricBand(p10=80.0, p50=100.0, p90=120.0)
    cost = MetricBand(p10=200.0, p50=250.0, p90=300.0)
    mc = _mc_run(failures=failures, downtime=downtime, cost=cost)
    pres = ContributionPresentation(horizon="per_year", year_choice=2020)
    fm_results = fm_results_from_mc_p50(project, mc)
    analytical = apply_presentation_scale_to_fm_rows(
        project,
        fm_results,
        build_rows(project, fm_results),
        presentation=pres,
        nb_filter=None,
    )[0]
    mc_scaled = apply_presentation_scale_to_mc_rows(
        project, mc, mc.rows, presentation=pres, nb_filter=None
    )[0]

    assert mc_scaled.failures_band.p50 == pytest.approx(analytical.expected_failures)
    assert mc_scaled.downtime_band.p50 == pytest.approx(
        analytical.expected_total_downtime_hr
    )
    assert mc_scaled.cost_band.p50 == pytest.approx(analytical.total_cost_eur)


def test_nb_filter_downtime_matches_analytical_scale() -> None:
    project = _project()
    failures = MetricBand(p10=8.0, p50=10.0, p90=12.0)
    downtime = MetricBand(p10=80.0, p50=100.0, p90=120.0)
    cost = MetricBand(p10=200.0, p50=250.0, p90=300.0)
    mc = _mc_run(failures=failures, downtime=downtime, cost=cost)
    pres = ContributionPresentation(horizon="lifecycle")
    nb_filter = EffectNbFilterSet(selected_klasse_ids=frozenset({"AV-1"}))
    fm_results = fm_results_from_mc_p50(project, mc)
    analytical = apply_presentation_scale_to_fm_rows(
        project,
        fm_results,
        build_rows(project, fm_results),
        presentation=pres,
        nb_filter=nb_filter,
    )[0]
    mc_scaled = apply_presentation_scale_to_mc_rows(
        project, mc, mc.rows, presentation=pres, nb_filter=nb_filter
    )[0]

    assert mc_scaled.downtime_band.p50 == pytest.approx(
        analytical.expected_total_downtime_hr
    )
