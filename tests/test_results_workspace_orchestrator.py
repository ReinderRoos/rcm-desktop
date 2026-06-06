"""Slice 61 — ResultsWorkspaceOrchestrator (Qt-vrij)."""
from __future__ import annotations

from pathlib import Path

from rcm_core.models import FMResult
from rcm_core.persistence import load_project

from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    CompareSlotSnapshot,
    CompareSlotState,
)
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.results_workspace_orchestrator import (
    ResultsWorkspaceOrchestrator,
    WorkspaceRenderContext,
    plan_compare_chrome,
)
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    MODE_LCC,
    ContributionPresentation,
    ResultsWorkspaceState,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.run_service import build_run_result
from rcm_desktop.adapter.workspace_render_index import WorkspaceRenderIndex


def _snap(**kwargs) -> WorkspaceStateSnapshot:
    base = ResultsWorkspaceState().snapshot()
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    data.update(kwargs)
    return WorkspaceStateSnapshot(**data)


def test_modus_switch_bijdragen_to_lcc_toolbar_visibility() -> None:
    prev = _snap(modus=MODE_BIJDRAGEN)
    curr = _snap(modus=MODE_LCC)
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(prev, curr)

    assert plan.detail_page_modus == MODE_LCC
    assert plan.bijdragen is None
    assert plan.lcc_toolbar is not None
    assert plan.lcc_toolbar.filter_bar_visible is True
    assert plan.lcc_toolbar.meekoppel_panel_visible is True
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.batch_faalwijzen_visible is False
    assert plan.fm_toolbar.clear_fm_inspector is True
    assert plan.pbs_tree_extended_selection is True
    assert plan.collapse.kpi is not None
    assert plan.collapse.lcc_whatif is not None
    assert plan.collapse.meekoppel is not None


def test_modus_switch_lcc_to_fm_detail() -> None:
    prev = _snap(modus=MODE_LCC)
    curr = _snap(modus=MODE_FM_DETAIL)
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(prev, curr)

    assert plan.lcc_toolbar is None
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.new_fm_visible is True
    assert plan.fm_toolbar.clear_fm_inspector is False
    assert plan.pbs_tree_extended_selection is False
    assert plan.collapse.kpi is None


def test_scope_change_sets_refresh_kpi() -> None:
    prev = _snap(scope_id=None, modus=MODE_LCC)
    curr = _snap(scope_id="PBS-1", modus=MODE_LCC)
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(prev, curr)
    assert plan.refresh_kpi is True


def test_metric_toggle_does_not_refresh_kpi() -> None:
    prev = _snap(metric=METRIC_KOSTEN, modus=MODE_BIJDRAGEN)
    curr = _snap(metric=METRIC_NIET_BESCHIKBAARHEID, modus=MODE_BIJDRAGEN)
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(prev, curr)
    assert plan.refresh_kpi is False


def test_bijdragen_horizon_and_nb_toggles() -> None:
    pres = ContributionPresentation(
        horizon="per_year",
        year_choice=2024,
        unavailability_display="percent",
    )
    snap = _snap(
        modus=MODE_BIJDRAGEN,
        metric=METRIC_NIET_BESCHIKBAARHEID,
        contribution_presentation=pres,
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)

    assert plan.bijdragen is not None
    assert plan.bijdragen.top10_subbar_visible is True
    assert plan.bijdragen.year_combo_visible is True
    assert plan.bijdragen.year_choice == 2024
    assert plan.bijdragen.nb_hours_visible is True
    assert plan.bijdragen.nb_percent_checked is True
    assert plan.bijdragen.horizon_per_year_checked is True


def test_bijdragen_faalmomenten_hides_nb_toggle() -> None:
    snap = _snap(modus=MODE_BIJDRAGEN, metric=METRIC_FAALMOMENTEN)
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)

    assert plan.bijdragen is not None
    assert plan.bijdragen.nb_hours_visible is False
    assert plan.bijdragen.horizon_lifecycle_visible is True


def test_compare_chrome_per_modus() -> None:
    bijdragen_compare = _snap(modus=MODE_BIJDRAGEN, compare_mode=True)
    plan_b = ResultsWorkspaceOrchestrator.plan_ui_sync(None, bijdragen_compare)
    assert plan_b.compare.bijdragen_compare_visible is True
    assert plan_b.compare.lcc_compare_visible is False

    lcc_compare = _snap(modus=MODE_LCC, compare_mode=True)
    plan_l = ResultsWorkspaceOrchestrator.plan_ui_sync(None, lcc_compare)
    assert plan_l.compare.lcc_compare_visible is True
    assert plan_l.compare.bijdragen_compare_visible is False


def test_lcc_filter_set_in_toolbar_plan() -> None:
    filters = LCCTypeFilterSet(cm=False, rev=True, in_task=False, tst=True, svo=True, wet=False)
    snap = _snap(modus=MODE_LCC, lcc_filters=filters)
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)

    assert plan.lcc_toolbar is not None
    assert plan.lcc_toolbar.lcc_filters == filters


def test_meekoppel_expand_triggers_ensure_whatif() -> None:
    prev = _snap(modus=MODE_LCC, meekoppel_collapsed_in_lcc=True)
    curr = _snap(modus=MODE_LCC, meekoppel_collapsed_in_lcc=False)
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(prev, curr)

    assert plan.collapse.meekoppel is not None
    assert plan.collapse.meekoppel.ensure_whatif_if_expanding is True
    assert plan.collapse.meekoppel.content_visible is True


def _session_with_run() -> ProjectSession:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    pbs_id = next(iter(project.pbs_items))
    fm_id = next(iter(project.faalwijzes))
    run = build_run_result(
        project,
        [
            FMResult(
                fm_id=fm_id,
                pbs_id=pbs_id,
                p_failure_lifecycle=0.5,
                expected_failures=5.0,
                expected_raw_downtime_hr=9.5,
                expected_detection_delay_hr=0.5,
                expected_total_downtime_hr=10.0,
                expected_pm_downtime_hr=0.0,
                expected_cm_cost_eur=60.0,
                pm_cost_eur=40.0,
                total_cost_eur=100.0,
                risk_contribution=0.25,
            )
        ],
    )
    return ProjectSession.from_parts(LoadedProject.from_core(project), run=run)


def _render_ctx(
    session: ProjectSession | None = None,
    *,
    slots: CompareSlotState | None = None,
    render_index: WorkspaceRenderIndex | None = None,
) -> WorkspaceRenderContext:
    return WorkspaceRenderContext(
        session=session,
        compare_slots=slots or CompareSlotState(),
        project_total_presentation=None,
        render_index=render_index or WorkspaceRenderIndex(),
        prev_lcc_snapshot=None,
    )


def test_plan_render_empty_without_session() -> None:
    plan = ResultsWorkspaceOrchestrator.plan_render(
        _snap(modus=MODE_BIJDRAGEN),
        _render_ctx(session=None),
    )
    assert plan.kind == "empty"


def test_plan_render_empty_without_run() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=None)
    plan = ResultsWorkspaceOrchestrator.plan_render(
        _snap(modus=MODE_BIJDRAGEN),
        _render_ctx(session=session),
    )
    assert plan.kind == "empty"


def test_plan_render_compare_placeholder_without_slots() -> None:
    session = _session_with_run()
    plan = ResultsWorkspaceOrchestrator.plan_render(
        _snap(modus=MODE_BIJDRAGEN, compare_mode=True),
        _render_ctx(session=session),
    )
    assert plan.kind == "compare_placeholder"


def test_plan_render_fm_detail() -> None:
    session = _session_with_run()
    plan = ResultsWorkspaceOrchestrator.plan_render(
        _snap(modus=MODE_FM_DETAIL),
        _render_ctx(session=session),
    )
    assert plan.kind == "fm"
    assert plan.fm is not None
    assert plan.fm.fm_rows


def test_plan_render_bijdragen_single() -> None:
    session = _session_with_run()
    plan = ResultsWorkspaceOrchestrator.plan_render(
        _snap(modus=MODE_BIJDRAGEN, compare_mode=False),
        _render_ctx(session=session),
    )
    assert plan.kind == "bijdragen"
    assert plan.bijdragen is not None
    assert plan.bijdragen.contribution_rows


def test_plan_render_bijdragen_compare_with_slot() -> None:
    session = _session_with_run()
    slots = CompareSlotState()
    overlay = PlanningOverlayState.inactive()
    slots.put(
        COMPARE_SLOT_A,
        CompareSlotSnapshot.from_motor_run(
            run_result=session.run,
            presentation=None,
            scenario_key="pm",
            overlay_at_run=overlay,
            label="A",
        ),
    )
    plan = ResultsWorkspaceOrchestrator.plan_render(
        _snap(modus=MODE_BIJDRAGEN, compare_mode=True),
        _render_ctx(session=session, slots=slots),
    )
    assert plan.kind == "bijdragen_compare"
    assert plan.compare_panels is not None
    assert len(plan.compare_panels) == 2
    assert plan.compare_panels[0].filled is True


def test_plan_render_all_splits_clears_render_index() -> None:
    session = _session_with_run()
    render_index = WorkspaceRenderIndex()
    render_index.get_or_build("CURRENT", None, "probe", lambda: "cached")
    stale_key = ("CURRENT", None, "probe")

    ResultsWorkspaceOrchestrator.plan_render(
        _snap(modus=MODE_BIJDRAGEN),
        _render_ctx(session=session, render_index=render_index),
        split_depth="all_splits",
    )
    assert stale_key not in render_index._cache


def test_plan_render_active_modus_only_preserves_render_index() -> None:
    session = _session_with_run()
    render_index = WorkspaceRenderIndex()
    render_index.get_or_build("CURRENT", None, "probe", lambda: "cached")

    ResultsWorkspaceOrchestrator.plan_render(
        _snap(modus=MODE_BIJDRAGEN),
        _render_ctx(session=session, render_index=render_index),
        split_depth="active_modus_only",
    )
    assert render_index._cache


def test_plan_workspace_tick_compose_ui_and_render() -> None:
    session = _session_with_run()
    prev = _snap(scope_id=None, modus=MODE_BIJDRAGEN)
    curr = _snap(scope_id="PBS-1", modus=MODE_BIJDRAGEN)
    tick = ResultsWorkspaceOrchestrator.plan_workspace_tick(
        prev,
        curr,
        _render_ctx(session=session),
    )
    assert tick.split_depth == "all_splits"
    assert tick.ui_sync.refresh_kpi is True
    assert tick.render.kind == "bijdragen"


def test_plan_compare_chrome_matches_ui_sync_compare() -> None:
    snap = _snap(modus=MODE_BIJDRAGEN, compare_mode=True)
    ui = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert plan_compare_chrome(snap) == ui.compare
