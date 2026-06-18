"""Slice 102-B1 — Faalwijze-analyse tabelregels in FM compare."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from rcm_core.simulation_engine import MetricBand

from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A, COMPARE_SLOT_B
from rcm_desktop.adapter.compare_view_service import ComparePanel
from rcm_desktop.adapter.faalwijze_analyse_service import (
    build_faalwijze_compare_presentation,
    compute_fm_compare_highlight,
)
from rcm_desktop.adapter.fm_compare_table_model import FMCompareTableModel
from rcm_desktop.adapter.result_view_service import FMResultRow
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    MODE_FM_DETAIL,
)
from rcm_desktop.adapter.results_workspace_orchestrator import (
    ResultsWorkspaceOrchestrator,
    _plan_output_fm_results_toolbar,
)
from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow
from rcm_desktop.adapter.workspace_view_service import FMDetailView
from rcm_desktop.adapter.workspace_view_registry import WORKSPACE_VIEW_REGISTRY, chrome_for_view
from rcm_desktop.theme.dp_tokens import DP_WARNING_BG
from tests.test_desktop_results_workspace_window import _ensure_app


def _analytical_row(
    fm_id: str,
    *,
    failures: float,
    cost: float = 100.0,
    downtime: float = 10.0,
    label: str = "Test",
) -> FMResultRow:
    return FMResultRow(
        fm_id=fm_id,
        faalwijze_omschrijving=label,
        pbs_id="PBS-1",
        bouwdeel_naam="BD",
        expected_failures=failures,
        expected_total_downtime_hr=downtime,
        total_cost_eur=cost,
    )


def _mc_row(fm_id: str, *, failures_p50: float, cost_p50: float = 100.0) -> FMMCResultRow:
    band_f = MetricBand(p10=failures_p50, p50=failures_p50, p90=failures_p50)
    band_d = MetricBand(p10=10.0, p50=10.0, p90=10.0)
    band_c = MetricBand(p10=cost_p50, p50=cost_p50, p90=cost_p50)
    return FMMCResultRow(
        fm_id=fm_id,
        faalwijze_omschrijving=fm_id,
        bouwdeel_naam="BD",
        failures_band=band_f,
        downtime_band=band_d,
        cost_band=band_c,
        is_nmf=False,
        rf=0.0,
    )


def _panels(
    rows_a: tuple[FMResultRow, ...] = (),
    rows_b: tuple[FMResultRow, ...] = (),
    *,
    mc_a: tuple[FMMCResultRow, ...] | None = None,
    mc_b: tuple[FMMCResultRow, ...] | None = None,
) -> tuple[ComparePanel, ComparePanel]:
    fm_a = FMDetailView(
        fm_rows=rows_a,
        mc_rows=mc_a or (),
        is_mc_mode=mc_a is not None,
    )
    fm_b = FMDetailView(
        fm_rows=rows_b,
        mc_rows=mc_b or (),
        is_mc_mode=mc_b is not None,
    )
    return (
        ComparePanel(slot_key=COMPARE_SLOT_A, label="S1", filled=True, fm=fm_a),
        ComparePanel(slot_key=COMPARE_SLOT_B, label="S2", filled=True, fm=fm_b),
    )


def test_compute_fm_compare_highlight_above_threshold() -> None:
    assert compute_fm_compare_highlight(100.0, 130.0) is True


def test_compute_fm_compare_highlight_false_when_s1_zero() -> None:
    assert compute_fm_compare_highlight(0.0, 50.0) is False


def test_compute_fm_compare_highlight_false_when_difference_small() -> None:
    assert compute_fm_compare_highlight(100.0, 115.0) is False


def test_build_faalwijze_compare_union_sort_and_highlight() -> None:
    panels = _panels(
        (
            _analytical_row("FM-A", failures=50.0, label="A"),
            _analytical_row("FM-B", failures=100.0, label="B"),
        ),
        (
            _analytical_row("FM-B", failures=150.0, label="B"),
            _analytical_row("FM-C", failures=5.0, label="C"),
        ),
    )
    pres = build_faalwijze_compare_presentation(panels, metric=METRIC_FAALMOMENTEN)
    assert [row.fm_id for row in pres.rows] == ["FM-B", "FM-A", "FM-C"]
    fm_b = pres.rows[0]
    assert fm_b.highlight is True
    assert fm_b.s1 == 100.0
    assert fm_b.s2 == 150.0
    fm_a = pres.rows[1]
    assert fm_a.s2 is None
    assert fm_a.highlight is False


def test_build_faalwijze_compare_metric_switch() -> None:
    panels = _panels(
        (_analytical_row("FM-A", failures=10.0, cost=500.0),),
        (_analytical_row("FM-A", failures=20.0, cost=100.0),),
    )
    failures = build_faalwijze_compare_presentation(panels, metric=METRIC_FAALMOMENTEN)
    costs = build_faalwijze_compare_presentation(panels, metric=METRIC_KOSTEN)
    assert failures.rows[0].s1 == 10.0
    assert costs.rows[0].s1 == 500.0


def test_fm_compare_table_models_share_row_order() -> None:
    panels = _panels(
        (_analytical_row("FM-A", failures=10.0), _analytical_row("FM-B", failures=30.0)),
        (_analytical_row("FM-B", failures=40.0), _analytical_row("FM-C", failures=5.0)),
    )
    pres = build_faalwijze_compare_presentation(panels, metric=METRIC_FAALMOMENTEN)
    model_a = FMCompareTableModel(pres, slot_side="s1")
    model_b = FMCompareTableModel(pres, slot_side="s2")
    assert model_a.rowCount() == model_b.rowCount() == 3
    assert model_a.data(model_a.index(0, 0)) == model_b.data(model_b.index(0, 0)) == "FM-B"


def test_fm_compare_table_model_hides_nmf_rf_by_default() -> None:
    panels = _panels((_analytical_row("FM-A", failures=1.0, label="x"),))
    pres = build_faalwijze_compare_presentation(panels, metric=METRIC_FAALMOMENTEN)
    model = FMCompareTableModel(pres, slot_side="s1")
    assert model.columnCount() == 4


def test_fm_compare_table_model_shows_nmf_rf_when_enabled() -> None:
    app = _ensure_app()
    panels = _panels((_analytical_row("FM-A", failures=1.0),))
    pres = build_faalwijze_compare_presentation(panels, metric=METRIC_FAALMOMENTEN)
    model = FMCompareTableModel(pres, slot_side="s1", show_nmf_rf=True)
    assert model.columnCount() == 6


def test_fm_compare_table_model_highlight_background() -> None:
    app = _ensure_app()
    panels = _panels(
        (_analytical_row("FM-A", failures=100.0),),
        (_analytical_row("FM-A", failures=200.0),),
    )
    pres = build_faalwijze_compare_presentation(panels, metric=METRIC_FAALMOMENTEN)
    model = FMCompareTableModel(pres, slot_side="s1")
    bg = model.data(model.index(0, 3), Qt.BackgroundRole)
    assert isinstance(bg, QColor)
    assert bg.name().upper() == DP_WARNING_BG.upper()


def test_fm_toolbar_hides_inspector_in_compare_mode() -> None:
    from dataclasses import replace

    from rcm_desktop.adapter.results_workspace_state import ResultsWorkspaceState

    state = ResultsWorkspaceState()
    state.set_compare_mode(True)
    snapshot = replace(state.snapshot(), modus=MODE_FM_DETAIL)
    profile = chrome_for_view(WORKSPACE_VIEW_REGISTRY, snapshot.active_view_id)
    assert profile is not None
    toolbar = _plan_output_fm_results_toolbar(snapshot, profile)
    assert toolbar.fm_inspector_visible is False


def test_orchestrator_fm_compare_plan_includes_faalwijze_presentation() -> None:
    from dataclasses import replace

    from rcm_desktop.adapter.compare_slot_state import CompareSlotSnapshot, CompareSlotState
    from rcm_desktop.adapter.loaded_project import LoadedProject
    from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
    from rcm_desktop.adapter.project_session import ProjectSession
    from rcm_desktop.adapter.results_workspace_orchestrator import WorkspaceRenderContext
    from rcm_desktop.adapter.results_workspace_state import ResultsWorkspaceState
    from rcm_desktop.adapter.workspace_render_index import WorkspaceRenderIndex

    from tests.test_desktop_results_workspace_window import _done_run_for_fixture, _three_level_project

    project = _three_level_project()
    run = _done_run_for_fixture()
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=run)
    slots = CompareSlotState()
    overlay = PlanningOverlayState.inactive()
    for key, tag in ((COMPARE_SLOT_A, "a"), (COMPARE_SLOT_B, "b")):
        slots.put(
            key,
            CompareSlotSnapshot.from_motor_run(
                run_result=run,
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
    assert plan.faalwijze_bundle is not None
    assert plan.faalwijze_bundle.compare is not None
    assert len(plan.faalwijze_bundle.compare.rows) >= 1
