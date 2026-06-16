"""Slice 100 issues 07/08 — mixed compare + FM split orchestrator tests."""

from __future__ import annotations

from dataclasses import replace

from rcm_core.simulation_engine import MetricBand

from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    COMPARE_SLOT_B,
    CompareSlotSnapshot,
    CompareSlotState,
)
from rcm_desktop.adapter.compare_split_layout_service import compute_compare_split_layout
from rcm_desktop.adapter.compare_view_service import build_fm_compare_panels
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.results_workspace_orchestrator import (
    ResultsWorkspaceOrchestrator,
    WorkspaceRenderContext,
)
from rcm_desktop.adapter.results_workspace_state import (
    MODE_FM_DETAIL,
    MODE_LCC,
    ResultsWorkspaceState,
    _DEFAULT_SNAPSHOT,
)
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow, MCRunResult
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.workspace_render_index import WorkspaceRenderIndex

from tests.test_desktop_results_workspace_window import _three_level_project


def _run(tag: str, *, cost: float = 100.0) -> RunResult:
    return RunResult(
        status="done",
        summary=tag,
        metrics=RunMetrics(
            fm_result_count=1,
            total_lifecycle_faalmomenten=1.0,
            total_cost_eur=cost,
        ),
    )


def test_fm_compare_split_layout_horizontal():
    layout = compute_compare_split_layout(compare_mode=True, modus=MODE_FM_DETAIL)
    assert layout.compare_mode is True
    assert layout.orientation == "horizontal"


def test_mixed_mode_compare_panels_use_mc_and_analytical_slots():
    project = _three_level_project()
    session = ProjectSession.from_parts(LoadedProject.from_core(project))
    mc = MCRunResult(
        status="done",
        seed=3,
        n_completed=200,
        rows=(
            FMMCResultRow(
                fm_id="FM-1",
                faalwijze_omschrijving="x",
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
        CompareSlotSnapshot.from_motor_run(
            run_result=_run("s1", cost=50.0),
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay,
            label="S1 analytisch",
            run_mode=RunMode.ANALYTICAL,
        ),
    )
    slots.put(
        COMPARE_SLOT_B,
        CompareSlotSnapshot.from_mc_run(
            mc_run=mc,
            run_result=_run("p50", cost=20.0),
            presentation=None,
            scenario_key="pm",
            overlay_at_run=overlay,
            label="S2 MC",
        ),
    )
    panels = build_fm_compare_panels(session, _DEFAULT_SNAPSHOT, slots=slots)
    assert len(panels) == 2
    assert panels[0].fm is not None and not panels[0].fm.is_mc_mode
    assert panels[1].fm is not None and panels[1].fm.is_mc_mode
    assert panels[1].fm.mc_rows[0].cost_band.p50 == 20.0


def test_orchestrator_fm_compare_plan_when_both_filled():
    project = _three_level_project()
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=_run("live"))
    slots = CompareSlotState()
    overlay = PlanningOverlayState.inactive()
    for key, tag in ((COMPARE_SLOT_A, "a"), (COMPARE_SLOT_B, "b")):
        slots.put(
            key,
            CompareSlotSnapshot.from_motor_run(
                run_result=_run(tag),
                presentation=None,
                scenario_key=None,
                overlay_at_run=overlay,
                label=tag,
            ),
        )
    state = ResultsWorkspaceState()
    state.set_compare_mode(True)
    snapshot = replace(state.snapshot(), modus=MODE_FM_DETAIL)
    ctx = WorkspaceRenderContext(
        session=session,
        compare_slots=slots,
        project_total_presentation=None,
        render_index=WorkspaceRenderIndex(),
        prev_lcc_snapshot=None,
    )
    plan = ResultsWorkspaceOrchestrator.plan_render(snapshot, ctx)
    assert plan.kind == "fm_compare"
    assert plan.compare_panels is not None
    assert len(plan.compare_panels) == 2


def test_lcc_compare_still_planned_for_metric_modes():
    project = _three_level_project()
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=_run("live"))
    slots = CompareSlotState()
    overlay = PlanningOverlayState.inactive()
    for key in (COMPARE_SLOT_A, COMPARE_SLOT_B):
        slots.put(
            key,
            CompareSlotSnapshot.from_motor_run(
                run_result=_run(key),
                presentation=None,
                scenario_key=None,
                overlay_at_run=overlay,
                label=key,
            ),
        )
    state = ResultsWorkspaceState()
    state.set_compare_mode(True)
    for metric in ("kosten", "faalmomenten", "niet_beschikbaarheid"):
        snapshot = replace(state.snapshot(), modus=MODE_LCC, metric=metric)
        ctx = WorkspaceRenderContext(
            session=session,
            compare_slots=slots,
            project_total_presentation=None,
            render_index=WorkspaceRenderIndex(),
            prev_lcc_snapshot=None,
        )
        plan = ResultsWorkspaceOrchestrator.plan_render(snapshot, ctx)
        assert plan.kind == "lcc_compare"
