"""Slice 101 issue 07 — LCC compare MC slot without prior analytical session."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from rcm_core.engine import compute_all_fm_results
from rcm_core.persistence import load_project
from rcm_core.simulation_engine import MetricBand

from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    COMPARE_SLOT_B,
    CompareSlotSnapshot,
    CompareSlotState,
)
from rcm_desktop.adapter.compare_view_service import build_lcc_compare_panels
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.results_workspace_state import METRIC_KOSTEN, MODE_LCC, _DEFAULT_SNAPSHOT
from rcm_desktop.adapter.run_service import RunMetrics, RunResult, build_run_result
from rcm_desktop.adapter.simulation_engine_service import (
    FMMCResultRow,
    MCRunResult,
    run_monte_carlo,
)
from rcm_desktop.adapter.workspace_render_index import WorkspaceRenderIndex


def test_lcc_compare_mc_slot_without_live_analytical_run() -> None:
    project = load_project(Path("tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json"))
    mc = run_monte_carlo(project, n=200, seed=42)
    anal_run = build_run_result(project, list(compute_all_fm_results(project).values()))
    slots = CompareSlotState()
    overlay = PlanningOverlayState.inactive()
    slots.put(
        COMPARE_SLOT_A,
        CompareSlotSnapshot.from_mc_run(
            mc_run=mc,
            run_result=RunResult(
                status="done",
                summary="stub",
                metrics=RunMetrics(
                    fm_result_count=0,
                    total_lifecycle_faalmomenten=0.0,
                    total_cost_eur=0.0,
                ),
            ),
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay,
            label="MC",
        ),
    )
    slots.put(
        COMPARE_SLOT_B,
        CompareSlotSnapshot.from_motor_run(
            run_result=anal_run,
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay,
            label="Analytical",
        ),
    )
    session = ProjectSession.from_parts(
        LoadedProject.from_core(project),
        run=None,
        mc_run=mc,
    )
    workspace = replace(_DEFAULT_SNAPSHOT, modus=MODE_LCC, metric=METRIC_KOSTEN)

    panels = build_lcc_compare_panels(
        session,
        workspace,
        slots=slots,
        render_index=WorkspaceRenderIndex(),
        prev_snapshot=None,
    )

    assert panels[0].lcc is not None and panels[0].lcc.curve is not None
    assert panels[0].lcc.curve.display_buckets
    assert panels[1].lcc is not None and panels[1].lcc.curve is not None


def test_lcc_compare_mc_slot_rebuilds_from_fm_results_when_run_stub() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    pbs_id = next(iter(project.pbs_items))
    fm_id = next(iter(project.faalwijzes))
    mc = MCRunResult(
        status="done",
        seed=1,
        n_completed=500,
        fm_results={
            fm_id: __import__(
                "rcm_core.simulation_engine", fromlist=["FMMCResult"]
            ).FMMCResult(
                fm_id=fm_id,
                pbs_id=pbs_id,
                failures=MetricBand(p10=1.0, p50=2.0, p90=3.0),
                downtime_hr=MetricBand(p10=1.0, p50=2.0, p90=3.0),
                total_cost_eur=MetricBand(p10=10.0, p50=20.0, p90=30.0),
                n_completed=500,
                seed=1,
            ),
        },
        rows=(
            FMMCResultRow(
                fm_id=fm_id,
                faalwijze_omschrijving="Synth",
                bouwdeel_naam="BD",
                failures_band=MetricBand(p10=1.0, p50=2.0, p90=3.0),
                downtime_band=MetricBand(p10=1.0, p50=2.0, p90=3.0),
                cost_band=MetricBand(p10=10.0, p50=20.0, p90=30.0),
                is_nmf=False,
                rf=0.0,
            ),
        ),
    )
    slots = CompareSlotState()
    overlay = PlanningOverlayState.inactive()
    slots.put(
        COMPARE_SLOT_A,
        CompareSlotSnapshot.from_mc_run(
            mc_run=mc,
            run_result=RunResult(
                status="done",
                summary="empty",
                metrics=RunMetrics(
                    fm_result_count=0,
                    total_lifecycle_faalmomenten=0.0,
                    total_cost_eur=0.0,
                ),
            ),
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay,
            label="MC",
        ),
    )
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=None, mc_run=mc)
    workspace = replace(_DEFAULT_SNAPSHOT, modus=MODE_LCC, metric=METRIC_KOSTEN)

    panels = build_lcc_compare_panels(
        session,
        workspace,
        slots=slots,
        render_index=WorkspaceRenderIndex(),
        prev_snapshot=None,
    )

    assert panels[0].lcc is not None and panels[0].lcc.curve is not None
    assert panels[0].lcc.curve.display_buckets
