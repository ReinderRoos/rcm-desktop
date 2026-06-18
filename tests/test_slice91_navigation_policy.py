"""Slice 91 issue 03 — navigatiepolicy Input → Faalwijzen."""

from __future__ import annotations

from rcm_desktop.adapter.results_workspace_state import (
    MODE_LCC,
    ResultsWorkspaceState,
)
from rcm_desktop.adapter.workspace_navigation_policy import resolve_view_for_side_switch
from rcm_desktop.adapter.workspace_view_registry import SIDE_INPUT, SIDE_OUTPUT


def test_policy_first_input_visit_forces_faalwijzen() -> None:
    view_id, pending = resolve_view_for_side_switch(
        side=SIDE_INPUT,
        sticky_view_by_side={SIDE_INPUT: "input.rev_tasks", SIDE_OUTPUT: "output.top_10"},
        first_input_visit_pending=True,
    )
    assert view_id == "input.faalwijzen"
    assert pending is False


def test_policy_after_first_visit_uses_sticky() -> None:
    view_id, pending = resolve_view_for_side_switch(
        side=SIDE_INPUT,
        sticky_view_by_side={SIDE_INPUT: "input.rev_tasks", SIDE_OUTPUT: "output.top_10"},
        first_input_visit_pending=False,
    )
    assert view_id == "input.rev_tasks"
    assert pending is False


def test_first_input_visit_forces_faalwijzen_despite_restored_sticky() -> None:
    state = ResultsWorkspaceState()
    state.restore_navigation(
        SIDE_OUTPUT,
        {SIDE_INPUT: "input.rev_tasks", SIDE_OUTPUT: "output.lcc_plot"},
    )
    state.set_workspace_side(SIDE_INPUT)
    snap = state.snapshot()
    assert snap.active_view_id == "input.faalwijzen"
    assert snap.workspace_side == SIDE_INPUT


def test_second_input_visit_restores_sticky_input_view() -> None:
    state = ResultsWorkspaceState()
    state.restore_navigation(
        SIDE_OUTPUT,
        {SIDE_INPUT: "input.rev_tasks", SIDE_OUTPUT: "output.lcc_plot"},
    )
    state.set_workspace_side(SIDE_INPUT)
    state.set_active_view("input.rev_tasks")
    state.set_workspace_side(SIDE_OUTPUT)
    state.set_workspace_side(SIDE_INPUT)
    snap = state.snapshot()
    assert snap.active_view_id == "input.rev_tasks"


def test_reset_for_new_project_resets_input_sticky_and_first_visit() -> None:
    state = ResultsWorkspaceState()
    state.set_active_view("input.rev_tasks")
    state.set_workspace_side(SIDE_OUTPUT)
    state.reset_for_new_project()
    assert state.sticky_views_by_side()[SIDE_INPUT] == "input.faalwijzen"
    state.set_workspace_side(SIDE_INPUT)
    assert state.snapshot().active_view_id == "input.faalwijzen"


def test_sticky_output_view_unaffected_by_input_policy() -> None:
    state = ResultsWorkspaceState()
    state.set_active_view("output.lcc_plot")
    state.set_workspace_side(SIDE_INPUT)
    state.set_workspace_side(SIDE_OUTPUT)
    snap = state.snapshot()
    assert snap.active_view_id == "output.lcc_plot"
    assert snap.modus == MODE_LCC
