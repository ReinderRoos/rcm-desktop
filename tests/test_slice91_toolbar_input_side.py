"""Slice 91 issue 02 — toolbar side-aware op Input-zijde."""

from __future__ import annotations

from rcm_desktop.adapter.results_workspace_orchestrator import ResultsWorkspaceOrchestrator
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_BIJDRAGEN,
    MODE_LCC,
    ResultsWorkspaceState,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.workspace_view_registry import SIDE_INPUT, SIDE_OUTPUT


def _snap(**kwargs) -> WorkspaceStateSnapshot:
    base = ResultsWorkspaceState().snapshot()
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    data.update(kwargs)
    return WorkspaceStateSnapshot(**data)


def test_shared_toolbar_hidden_on_input_faalwijzen_despite_lcc_modus() -> None:
    snap = _snap(
        workspace_side=SIDE_INPUT,
        active_view_id="input.faalwijzen",
        modus=MODE_LCC,
        metric=METRIC_NIET_BESCHIKBAARHEID,
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert plan.shared_toolbar.effect_nb_filter_in_shared_row is False
    assert plan.lcc_toolbar is None
    assert plan.bijdragen is None


def test_shared_toolbar_visible_on_output_lcc_with_nb_metric() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.lcc_plot",
        modus=MODE_LCC,
        metric=METRIC_NIET_BESCHIKBAARHEID,
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert plan.shared_toolbar.effect_nb_filter_in_shared_row is True
    assert plan.lcc_toolbar is not None
    assert plan.lcc_toolbar.effect_nb_filter_visible is True


def test_bijdragen_toolbar_hidden_on_input_side() -> None:
    snap = _snap(
        workspace_side=SIDE_INPUT,
        active_view_id="input.faalwijzen",
        modus=MODE_BIJDRAGEN,
        metric=METRIC_NIET_BESCHIKBAARHEID,
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert plan.bijdragen is None
