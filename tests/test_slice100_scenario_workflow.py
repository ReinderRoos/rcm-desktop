"""Slice 100 issue 04 — scenario slot state + freeze lifecycle (TDD)."""

from __future__ import annotations

from rcm_desktop.adapter.compare_slot_state import CompareSlotSnapshot
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.simulation_job_service import RunMode


def _run(tag: str = "r") -> RunResult:
    return RunResult(
        status="done",
        summary=tag,
        metrics=RunMetrics(
            fm_result_count=0,
            total_lifecycle_faalmomenten=0.0,
            total_cost_eur=0.0,
        ),
    )


def test_compare_slot_snapshot_carries_run_mode():
    snap = CompareSlotSnapshot.from_motor_run(
        run_result=_run("a"),
        presentation=None,
        scenario_key=None,
        overlay_at_run=PlanningOverlayState.inactive(),
        label="Scenario 1 — analytisch",
        run_mode=RunMode.ANALYTICAL,
    )
    assert snap.run_mode is RunMode.ANALYTICAL


def test_freeze_live_as_scenario_1_preserves_analytical_run():
    from rcm_desktop.adapter.scenario_workflow_service import (
        LiveRunSnapshot,
        ScenarioWorkflowService,
    )

    live_run = _run("live")
    overlay = PlanningOverlayState.inactive()
    svc = ScenarioWorkflowService()
    svc.freeze_live_as_scenario_1(
        LiveRunSnapshot(
            run_mode=RunMode.ANALYTICAL,
            run_result=live_run,
            mc_run=None,
            overlay=overlay,
            scenario_key=None,
            presentation=None,
        )
    )

    snap = svc.get_scenario_1()
    assert snap is not None
    assert snap.run_result is live_run
    assert snap.run_mode is RunMode.ANALYTICAL
    assert snap.overlay_at_run is overlay
    assert "analytisch" in snap.label.lower()


def test_freeze_live_as_scenario_1_preserves_mc_run():
    from rcm_core.simulation_engine import MetricBand
    from rcm_desktop.adapter.scenario_workflow_service import (
        LiveRunSnapshot,
        ScenarioWorkflowService,
    )
    from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow, MCRunResult

    mc = MCRunResult(
        status="done",
        seed=11,
        n_completed=1000,
        rows=(
            FMMCResultRow(
                fm_id="FM-1",
                faalwijze_omschrijving="x",
                bouwdeel_naam="BD",
                failures_band=MetricBand(p10=1.0, p50=2.0, p90=3.0),
                downtime_band=MetricBand(p10=1.0, p50=2.0, p90=3.0),
                cost_band=MetricBand(p10=1.0, p50=2.0, p90=3.0),
                is_nmf=False,
                rf=0.0,
            ),
        ),
    )
    p50_run = _run("p50")
    overlay = PlanningOverlayState.inactive()
    svc = ScenarioWorkflowService()
    svc.freeze_live_as_scenario_1(
        LiveRunSnapshot(
            run_mode=RunMode.MONTE_CARLO,
            run_result=p50_run,
            mc_run=mc,
            overlay=overlay,
            scenario_key="pm",
            presentation=None,
        )
    )

    snap = svc.get_scenario_1()
    assert snap is not None
    assert snap.run_mode is RunMode.MONTE_CARLO
    assert snap.mc_run is mc
    assert "MC N=1000" in snap.label


def test_both_filled_false_until_scenario_2():
    from rcm_desktop.adapter.scenario_workflow_service import (
        LiveRunSnapshot,
        ScenarioWorkflowService,
    )

    svc = ScenarioWorkflowService()
    assert not svc.both_filled()
    svc.freeze_live_as_scenario_1(
        LiveRunSnapshot(
            run_mode=RunMode.ANALYTICAL,
            run_result=_run("s1"),
            mc_run=None,
            overlay=PlanningOverlayState.inactive(),
            scenario_key=None,
            presentation=None,
        )
    )
    assert svc.has("A")
    assert not svc.both_filled()


def test_both_filled_true_when_scenario_1_and_2_present():
    from rcm_desktop.adapter.scenario_workflow_service import (
        LiveRunSnapshot,
        ScenarioWorkflowService,
    )

    overlay = PlanningOverlayState.inactive()
    svc = ScenarioWorkflowService()
    live = LiveRunSnapshot(
        run_mode=RunMode.ANALYTICAL,
        run_result=_run("live"),
        mc_run=None,
        overlay=overlay,
        scenario_key=None,
        presentation=None,
    )
    svc.freeze_live_as_scenario_1(live)
    svc.put_scenario_2(live)
    assert svc.both_filled()


def test_failed_scenario_2_put_leaves_scenario_1_intact():
    import pytest

    from rcm_desktop.adapter.scenario_workflow_service import (
        LiveRunSnapshot,
        ScenarioWorkflowService,
    )

    overlay = PlanningOverlayState.inactive()
    svc = ScenarioWorkflowService()
    svc.freeze_live_as_scenario_1(
        LiveRunSnapshot(
            run_mode=RunMode.ANALYTICAL,
            run_result=_run("s1"),
            mc_run=None,
            overlay=overlay,
            scenario_key=None,
            presentation=None,
        )
    )
    s1 = svc.get_scenario_1()
    failed = RunResult(
        status="error",
        summary="fail",
        metrics=RunMetrics(
            fm_result_count=0,
            total_lifecycle_faalmomenten=0.0,
            total_cost_eur=0.0,
        ),
    )
    with pytest.raises(ValueError, match="voltooide"):
        svc.put_scenario_2(
            LiveRunSnapshot(
                run_mode=RunMode.ANALYTICAL,
                run_result=failed,
                mc_run=None,
                overlay=overlay,
                scenario_key=None,
                presentation=None,
            )
        )
    assert svc.get_scenario_1() is s1
    assert not svc.both_filled()


def test_clear_all_wipes_scenario_slots():
    from rcm_desktop.adapter.scenario_workflow_service import (
        LiveRunSnapshot,
        ScenarioWorkflowService,
    )

    svc = ScenarioWorkflowService()
    live = LiveRunSnapshot(
        run_mode=RunMode.ANALYTICAL,
        run_result=_run("live"),
        mc_run=None,
        overlay=PlanningOverlayState.inactive(),
        scenario_key=None,
        presentation=None,
    )
    svc.freeze_live_as_scenario_1(live)
    svc.put_scenario_2(live)
    svc.clear_all()
    assert not svc.has("A")
    assert not svc.has("B")
    assert not svc.both_filled()
