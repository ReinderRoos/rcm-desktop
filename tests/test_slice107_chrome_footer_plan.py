"""Slice 107 issue 03 — WorkspaceChromeFooterPlan."""

from __future__ import annotations

from rcm_desktop.adapter.results_workspace_orchestrator import (
    ResultsWorkspaceOrchestrator,
    plan_chrome_footer,
)
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_FM_DETAIL,
    MODE_LCC,
    ResultsWorkspaceState,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.workspace_view_registry import SIDE_OUTPUT


def _snap(**kwargs) -> WorkspaceStateSnapshot:
    base = ResultsWorkspaceState().snapshot()
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    data.update(kwargs)
    return WorkspaceStateSnapshot(**data)


def test_kpi_footer_visible_without_context() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.kpi_overview",
        modus="kpi_overview",
    )
    plan = plan_chrome_footer(snap)
    assert plan.context_label == ""
    assert plan.middle_chrome_visible is False
    assert plan.lcc_measure_stack_visible is False


def test_topx_footer_has_metric_chrome() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.fm_results",
        modus=MODE_FM_DETAIL,
    )
    plan = plan_chrome_footer(snap)
    assert plan.middle_chrome_visible is True
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.metric_combo_visible is True


def test_lcc_footer_vertical_measure_stack_when_kosten() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.lcc_plot",
        modus=MODE_LCC,
        metric=METRIC_KOSTEN,
    )
    plan = plan_chrome_footer(snap)
    assert plan.lcc_measure_stack_visible is True
    assert plan.lcc_whatif_light_visible is True


def test_lcc_footer_no_measure_stack_for_nb_metric() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.lcc_plot",
        modus=MODE_LCC,
        metric=METRIC_NIET_BESCHIKBAARHEID,
    )
    plan = plan_chrome_footer(snap)
    assert plan.lcc_measure_stack_visible is False


def test_orchestrator_includes_chrome_footer_plan() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.lcc_plot",
        modus=MODE_LCC,
    )
    ui = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert ui.chrome_footer.context_label == ""
    assert ui.view_title
