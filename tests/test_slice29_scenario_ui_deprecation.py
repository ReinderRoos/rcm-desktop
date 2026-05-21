"""Slice 29 issue 06 — werkruimte: geen CM/PM-scenario als standaardpad."""

from __future__ import annotations

from rcm_desktop import messages
from rcm_desktop.adapter.results_workspace_state import (
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    MODE_LCC,
)
from rcm_desktop.adapter.scenario_slot_state import (
    SCENARIO_KEY_CM,
    SCENARIO_KEY_PM,
    ScenarioSlotState,
)
from rcm_desktop.adapter.workspace_split_layout import (
    SPLIT_NONE,
    compute_split_layout,
)


def _state_with_both_slots() -> ScenarioSlotState:
    state = ScenarioSlotState()
    for key in (SCENARIO_KEY_CM, SCENARIO_KEY_PM):
        state.put(key, run_result=object(), project_snapshot=object())
    return state


def test_compute_split_layout_never_enables_scenario_split():
    """Ook met gevulde scenario-slots blijft de werkruimte single-run (slice 29 #06)."""
    state = _state_with_both_slots()
    for mode in (MODE_BIJDRAGEN, MODE_LCC, MODE_FM_DETAIL):
        layout = compute_split_layout(state, mode)
        assert layout.orientation == SPLIT_NONE
        assert layout.scenario_mode is False
        assert layout.cm_slot is None
        assert layout.pm_slot is None


def test_workspace_copy_does_not_promote_cm_pm_scenario_compare():
    assert "vergelijk scenario" not in messages.WORKSPACE_DETAIL_EMPTY_STATE.lower()
    tooltip = messages.WORKSPACE_START_ANALYSE_BUTTON_TOOLTIP.lower()
    assert "what-if" in tooltip
    assert "vergelijk scenario" not in tooltip


def test_run_button_tooltip_mentions_what_if_not_pm_scenario():
    tooltip = messages.RUN_BUTTON_TOOLTIP.lower()
    assert "pm-scenario" not in tooltip
    assert "what-if" in tooltip
