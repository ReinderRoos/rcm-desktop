"""Slice 100 — MC vs analytical compare must use per-slot runs for Top10/LCC."""

from __future__ import annotations

from dataclasses import replace

from rcm_core.models import FMHorizonProfile, FMResult
from rcm_core.persistence import load_project
from rcm_core.simulation_engine import MetricBand

from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    COMPARE_SLOT_B,
    CompareSlotSnapshot,
    CompareSlotState,
)
from rcm_desktop.adapter.compare_view_service import (
    build_bijdragen_compare_panels,
    build_lcc_compare_panels,
)
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.presentation_cache_service import build_contribution_presentation
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_BIJDRAGEN,
    MODE_LCC,
    SOURCE_FAALWIJZE,
    _DEFAULT_SNAPSHOT,
)
from rcm_desktop.adapter.run_service import RunMetrics, RunResult, build_run_result
from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow, MCRunResult
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.workspace_render_index import WorkspaceRenderIndex
from pathlib import Path


def _fm_with_horizon(*, pbs_id: str, cor_eur: tuple[float, ...], downtime_hr: float) -> FMResult:
    n = len(cor_eur)
    hp = FMHorizonProfile(
        cor_eur=cor_eur,
        cor_downtime_hr=(0.0,) * n,
        hidden_nb_hr=(downtime_hr / n,) * n,
    )
    total = sum(cor_eur)
    return FMResult(
        fm_id=f"FM-{pbs_id}",
        pbs_id=pbs_id,
        p_failure_lifecycle=0.5,
        expected_failures=5.0,
        expected_raw_downtime_hr=downtime_hr * 0.9,
        expected_detection_delay_hr=downtime_hr * 0.1,
        expected_total_downtime_hr=downtime_hr,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=total,
        pm_cost_eur=0.0,
        total_cost_eur=total,
        risk_contribution=0.25,
        horizon_profile=hp,
    )


def _mc_slot(
    *,
    p50_run: RunResult,
    seed: int = 3,
    presentation=None,
) -> CompareSlotSnapshot:
    mc = MCRunResult(
        status="done",
        seed=seed,
        n_completed=500,
        rows=(
            FMMCResultRow(
                fm_id="FM-x",
                faalwijze_omschrijving="Synth",
                bouwdeel_naam="BD",
                failures_band=MetricBand(p10=1.0, p50=50.0, p90=99.0),
                downtime_band=MetricBand(p10=10.0, p50=500.0, p90=900.0),
                cost_band=MetricBand(p10=100.0, p50=5000.0, p90=9000.0),
                is_nmf=False,
                rf=0.0,
            ),
        ),
    )
    return CompareSlotSnapshot.from_mc_run(
        mc_run=mc,
        run_result=p50_run,
        presentation=presentation,
        scenario_key="pm",
        overlay_at_run=PlanningOverlayState.inactive(),
        label="Scenario 1 — MC N=500",
    )


def test_compare_bijdragen_ignores_shared_presentation_cache_per_slot():
    """Regression: frozen presentation cache must not mask slot run differences."""
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    pbs_id = next(iter(project.pbs_items))
    run_low = build_run_result(
        project, [_fm_with_horizon(pbs_id=pbs_id, cor_eur=(40.0, 40.0), downtime_hr=23.54)]
    )
    run_high = build_run_result(
        project, [_fm_with_horizon(pbs_id=pbs_id, cor_eur=(400.0, 400.0), downtime_hr=230.0)]
    )
    shared_presentation = build_contribution_presentation(project, run_low)
    slots = CompareSlotState()
    slots.put(COMPARE_SLOT_A, _mc_slot(p50_run=run_low, presentation=shared_presentation))
    slots.put(
        COMPARE_SLOT_B,
        CompareSlotSnapshot.from_motor_run(
            run_result=run_high,
            presentation=shared_presentation,
            scenario_key=None,
            overlay_at_run=PlanningOverlayState.inactive(),
            label="S2 analytisch",
            run_mode=RunMode.ANALYTICAL,
        ),
    )
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=run_high)
    workspace = replace(
        _DEFAULT_SNAPSHOT,
        modus=MODE_BIJDRAGEN,
        source=SOURCE_FAALWIJZE,
        metric=METRIC_NIET_BESCHIKBAARHEID,
    )

    panels = build_bijdragen_compare_panels(
        session,
        workspace,
        slots=slots,
        render_index=WorkspaceRenderIndex(),
        project_total_presentation=None,
    )

    assert panels[0].bijdragen is not None and panels[1].bijdragen is not None
    assert not panels[0].bijdragen.from_presentation_cache
    assert not panels[1].bijdragen.from_presentation_cache
    val_a = panels[0].bijdragen.contribution_rows[0].value
    val_b = panels[1].bijdragen.contribution_rows[0].value
    assert val_a != val_b


def test_compare_lcc_mc_p50_vs_analytical_uses_distinct_slot_runs():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    pbs_id = next(iter(project.pbs_items))
    run_mc = build_run_result(
        project,
        [_fm_with_horizon(pbs_id=pbs_id, cor_eur=(340.99, 100.0, 50.0), downtime_hr=10.0)],
    )
    run_analytical = build_run_result(
        project,
        [_fm_with_horizon(pbs_id=pbs_id, cor_eur=(120.0, 120.0, 120.0), downtime_hr=5.0)],
    )
    slots = CompareSlotState()
    slots.put(COMPARE_SLOT_A, _mc_slot(p50_run=run_mc))
    slots.put(
        COMPARE_SLOT_B,
        CompareSlotSnapshot.from_motor_run(
            run_result=run_analytical,
            presentation=None,
            scenario_key=None,
            overlay_at_run=PlanningOverlayState.inactive(),
            label="S2 analytisch",
        ),
    )
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=run_analytical)
    workspace = replace(_DEFAULT_SNAPSHOT, modus=MODE_LCC, metric=METRIC_KOSTEN)

    panels = build_lcc_compare_panels(
        session,
        workspace,
        slots=slots,
        render_index=WorkspaceRenderIndex(),
        prev_snapshot=None,
    )

    assert panels[0].lcc is not None and panels[1].lcc is not None
    buckets_a = panels[0].lcc.curve.display_buckets
    buckets_b = panels[1].lcc.curve.display_buckets
    assert buckets_a and buckets_b

    def _year_total(bucket) -> float:
        return bucket.correctief_eur + bucket.preventief_eur

    assert _year_total(buckets_a[0]) != _year_total(buckets_b[0])
