"""Slice 79 issue 01 — werkruimte-navigatiestate (Qt-vrij)."""

from __future__ import annotations

from rcm_desktop.adapter.results_workspace_state import (
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    MODE_LCC,
    ResultsWorkspaceState,
)
from rcm_desktop.adapter.workspace_view_registry import SIDE_INPUT, SIDE_OUTPUT


def test_default_navigation_starts_on_output_top_10() -> None:
    snap = ResultsWorkspaceState().snapshot()
    assert snap.workspace_side == SIDE_OUTPUT
    assert snap.active_view_id == "output.top_10"
    assert snap.modus == MODE_BIJDRAGEN


def test_set_active_view_switches_legacy_modus() -> None:
    state = ResultsWorkspaceState()
    state.set_active_view("output.fm_results")
    snap = state.snapshot()
    assert snap.active_view_id == "output.fm_results"
    assert snap.modus == MODE_FM_DETAIL
    assert snap.workspace_side == SIDE_OUTPUT


def test_set_active_view_ltap_switches_to_lcc_modus() -> None:
    state = ResultsWorkspaceState()
    state.set_active_view("output.ltap")
    snap = state.snapshot()
    assert snap.active_view_id == "output.ltap"
    assert snap.modus == MODE_LCC
    assert snap.workspace_side == SIDE_OUTPUT


def test_set_workspace_side_switches_to_input_faalwijzen_view() -> None:
    state = ResultsWorkspaceState()
    state.set_active_view("output.lcc_plot")
    state.set_workspace_side(SIDE_INPUT)
    snap = state.snapshot()
    assert snap.workspace_side == SIDE_INPUT
    assert snap.active_view_id == "input.faalwijzen"
    assert snap.modus == MODE_LCC


def test_set_workspace_side_restores_sticky_output_view() -> None:
    state = ResultsWorkspaceState()
    state.set_active_view("output.lcc_plot")
    state.set_workspace_side(SIDE_INPUT)
    state.set_workspace_side(SIDE_OUTPUT)
    snap = state.snapshot()
    assert snap.active_view_id == "output.lcc_plot"
    assert snap.modus == MODE_LCC
