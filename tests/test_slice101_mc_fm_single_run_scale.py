"""Slice 101 issue 02 — single-run MC FM respects ContributionPresentation."""

from __future__ import annotations

import pytest

from rcm_core.config import RCMConfig
from rcm_core.models import Faalwijze, PBSItem, RCMProject
from rcm_core.simulation_engine import FMMCResult, MetricBand
from rcm_core.units import TimeDuration, TimeUnit
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.result_view_service import apply_presentation_scale_to_mc_rows
from rcm_desktop.adapter.results_workspace_state import (
    ContributionPresentation,
    ResultsWorkspaceState,
)
from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow, MCRunResult
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.workspace_view_service import build_fm_detail_view

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


def _mc_session(project: RCMProject) -> ProjectSession:
    failures = MetricBand(p10=8.0, p50=10.0, p90=12.0)
    downtime = MetricBand(p10=80.0, p50=100.0, p90=120.0)
    cost = MetricBand(p10=200.0, p50=250.0, p90=300.0)
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
    mc = MCRunResult(
        status="done",
        seed=1,
        n_completed=100,
        fm_results={"FM-1": mc_fm},
        rows=(row,),
    )
    return ProjectSession.from_parts(LoadedProject.from_core(project), mc_run=mc)


def test_build_fm_detail_view_mc_scales_to_per_year_average() -> None:
    project = _project()
    session = _mc_session(project)
    ws = ResultsWorkspaceState()
    ws.set_contribution_presentation(
        ContributionPresentation(horizon="per_year", year_choice="average")
    )
    expected = apply_presentation_scale_to_mc_rows(
        project,
        session.mc_run,
        session.mc_run.rows,
        presentation=ws.snapshot().contribution_presentation,
        nb_filter=None,
    )

    view = build_fm_detail_view(
        session, ws.snapshot(), run_mode=RunMode.MONTE_CARLO
    )
    assert view is not None
    assert view.mc_rows[0].cost_band.p50 == pytest.approx(
        expected[0].cost_band.p50
    )
    assert view.mc_rows[0].failures_band.p50 == pytest.approx(
        expected[0].failures_band.p50
    )
    assert view.mc_rows[0].cost_band.p50 < session.mc_run.rows[0].cost_band.p50
