"""Slice 101 issue 04 — mixed FM compare plausible at default horizon."""

from __future__ import annotations

import pytest

from rcm_core.config import RCMConfig
from rcm_core.engine import compute_all_fm_results
from rcm_core.models import Faalwijze, PBSItem, RCMProject
from rcm_core.simulation_engine import FMMCResult, MetricBand
from rcm_core.units import TimeDuration, TimeUnit
from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    COMPARE_SLOT_B,
    CompareSlotSnapshot,
    CompareSlotState,
)
from rcm_desktop.adapter.compare_view_service import build_fm_compare_panels
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.results_workspace_state import _DEFAULT_SNAPSHOT
from rcm_desktop.adapter.run_service import build_run_result
from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow, MCRunResult

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


def test_mixed_fm_compare_default_horizon_cost_ratio_plausible() -> None:
    project = _project()
    fm_results = list(compute_all_fm_results(project).values())
    analytical_run = build_run_result(project, fm_results, summary_prefix="Analytisch")
    fmr = fm_results[0]
    failures = MetricBand(
        p10=fmr.expected_failures * 0.8,
        p50=fmr.expected_failures,
        p90=fmr.expected_failures * 1.2,
    )
    downtime = MetricBand(
        p10=fmr.expected_total_downtime_hr * 0.8,
        p50=fmr.expected_total_downtime_hr,
        p90=fmr.expected_total_downtime_hr * 1.2,
    )
    cost = MetricBand(
        p10=fmr.total_cost_eur * 0.8,
        p50=fmr.total_cost_eur,
        p90=fmr.total_cost_eur * 1.2,
    )
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
    session = ProjectSession.from_parts(LoadedProject.from_core(project))
    overlay = PlanningOverlayState.inactive()
    slots = CompareSlotState()
    slots.put(
        COMPARE_SLOT_A,
        CompareSlotSnapshot.from_motor_run(
            run_result=analytical_run,
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay,
            label="Analytisch",
        ),
    )
    slots.put(
        COMPARE_SLOT_B,
        CompareSlotSnapshot.from_mc_run(
            mc_run=mc,
            run_result=build_run_result(project, fm_results, summary_prefix="MC P50"),
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay,
            label="MC",
        ),
    )

    panels = build_fm_compare_panels(session, _DEFAULT_SNAPSHOT, slots=slots)
    a_failures = panels[0].fm.fm_rows[0].expected_failures
    b_failures = panels[1].fm.mc_rows[0].failures_band.p50
    assert a_failures > 0.0 and b_failures > 0.0
    ratio = max(a_failures, b_failures) / min(a_failures, b_failures)
    assert ratio < 3.0, f"FM compare failure ratio {ratio} suggests horizon mismatch"
