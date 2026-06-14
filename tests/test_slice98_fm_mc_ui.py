"""Slice 98 issue 08 — FM MC bands presentation."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from rcm_core.config import RCMConfig
from rcm_core.models import FailureType, Faalwijze, Functie, PBSItem, RCMProject
from rcm_core.simulation_engine import MetricBand
from rcm_desktop.adapter.fm_mc_results_table_model import FMMCResultsTableModel
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow, MCRunResult, run_monte_carlo
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.workspace_view_service import build_fm_detail_view
from rcm_desktop.adapter.results_workspace_state import ResultsWorkspaceState


def _tiny_project() -> RCMProject:
    cfg = RCMConfig(lifecycle_years=80.0, modeljaar=2026, monte_carlo_n=500)
    pbs = PBSItem("PBS-1", "Obj", "El", "BD", bouwjaar=2000)
    func = Functie("F-1", "PBS-1", "Functie")
    fm = Faalwijze(
        "FM-R",
        "PBS-1",
        "F-1",
        "Random",
        failure_type=FailureType.RANDOM,
        mttf_jaar=10.0,
        cost_cm_eur=500.0,
    )
    return RCMProject(
        config=cfg,
        pbs_items={"PBS-1": pbs},
        functies={"F-1": func},
        faalwijzes={"FM-R": fm},
    )


def test_build_fm_detail_view_mc_mode_returns_bands():
    project = _tiny_project()
    mc = run_monte_carlo(project, n=200, seed=4)
    session = ProjectSession.from_parts(LoadedProject.from_core(project), mc_run=mc)
    ws = ResultsWorkspaceState()
    view = build_fm_detail_view(session, ws.snapshot(), run_mode=RunMode.MONTE_CARLO)
    assert view is not None
    assert view.is_mc_mode
    assert len(view.mc_rows) == 1
    assert view.mc_rows[0].failures_band.p10 <= view.mc_rows[0].failures_band.p50


def test_analytical_mode_unchanged_without_analytical_run():
    project = _tiny_project()
    mc = run_monte_carlo(project, n=200, seed=4)
    session = ProjectSession.from_parts(LoadedProject.from_core(project), mc_run=mc)
    ws = ResultsWorkspaceState()
    assert build_fm_detail_view(session, ws.snapshot(), run_mode=RunMode.ANALYTICAL) is None


def test_fmmc_table_model_shows_band_value(qtbot):
    row = FMMCResultRow(
        fm_id="FM-R",
        faalwijze_omschrijving="Random",
        bouwdeel_naam="BD",
        failures_band=MetricBand(p10=1.0, p50=2.0, p90=3.0),
        downtime_band=MetricBand(p10=10.0, p50=20.0, p90=30.0),
        cost_band=MetricBand(p10=100.0, p50=200.0, p90=300.0),
        is_nmf=False,
        rf=0.5,
    )
    model = FMMCResultsTableModel([row])
    display = model.data(model.index(0, 5))
    assert display is not None
    assert "2" in str(display)
    tooltip = model.data(model.index(0, 5), role=257)  # Qt.ToolTipRole == 257 in tests sometimes
    from PySide6.QtCore import Qt

    tooltip = model.data(model.index(0, 5), role=Qt.ToolTipRole)
    assert tooltip is not None
    assert "P10" in tooltip and "P90" in tooltip
