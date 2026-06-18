"""Slice 108 issue 04 — 3-rijen context filter."""

from __future__ import annotations

from rcm_desktop.adapter.faalwijze_analyse_service import fm_table_context_row_indices


def test_context_middle_row_shows_three() -> None:
    ids = ("A", "B", "C", "D", "E")
    assert fm_table_context_row_indices(ids, "C") == (1, 2, 3)


def test_context_first_row_no_placeholder() -> None:
    ids = ("A", "B", "C")
    assert fm_table_context_row_indices(ids, "A") == (0, 1)


def test_context_last_row_no_placeholder() -> None:
    ids = ("A", "B", "C")
    assert fm_table_context_row_indices(ids, "C") == (1, 2)


def test_context_single_row() -> None:
    assert fm_table_context_row_indices(("ONLY",), "ONLY") == (0,)


def test_step_fm_inspector_moves_in_list() -> None:
    from rcm_desktop.adapter.results_workspace_state import ResultsWorkspaceState

    state = ResultsWorkspaceState()
    state.open_fm_inspector_mode("B")
    state.step_fm_inspector(1, ("A", "B", "C"))
    assert state.snapshot().fm_inspector_fm_id == "C"
    state.step_fm_inspector(-1, ("A", "B", "C"))
    assert state.snapshot().fm_inspector_fm_id == "B"
