"""Slice 79 issue 01 — orchestrator navigatieplan (Qt-vrij)."""

from __future__ import annotations

from rcm_desktop.adapter.results_workspace_orchestrator import ResultsWorkspaceOrchestrator
from rcm_desktop.adapter.results_workspace_state import (
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    ResultsWorkspaceState,
)
from rcm_desktop.adapter.workspace_view_registry import SIDE_INPUT, SIDE_OUTPUT


def _snap(**kwargs):
    base = ResultsWorkspaceState().snapshot()
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    data.update(kwargs)
    from rcm_desktop.adapter.results_workspace_state import WorkspaceStateSnapshot

    return WorkspaceStateSnapshot(**data)


def test_navigation_plan_lists_output_views_with_ltap_disabled() -> None:
    snap = _snap(workspace_side=SIDE_OUTPUT, active_view_id="output.top_10", modus=MODE_BIJDRAGEN)
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap).navigation

    assert plan.workspace_side == SIDE_OUTPUT
    assert plan.side_output_checked is True
    assert plan.side_input_checked is False
    assert plan.active_view_id == "output.top_10"
    assert [item.view_id for item in plan.dropdown_items] == [
        "output.lcc_plot",
        "output.ltap",
        "output.fm_results",
    ]
    ltap = plan.dropdown_items[1]
    assert ltap.enabled is True
    assert plan.show_input_placeholder is False


def test_navigation_plan_shows_entity_grid_on_enabled_input_view() -> None:
    snap = _snap(
        workspace_side=SIDE_INPUT,
        active_view_id="input.faalwijzen",
        modus=MODE_FM_DETAIL,
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap).navigation

    assert plan.workspace_side == SIDE_INPUT
    assert plan.side_input_checked is True
    assert plan.show_input_placeholder is False
    assert plan.show_input_entity_grid is True
    assert all(item.enabled for item in plan.dropdown_items)
