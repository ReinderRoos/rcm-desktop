"""Tests for Qt-free workspace split-layout adapter (slice 23, issue 07).

Bepaalt op basis van scenario-slot-state + modus:
- of de werkruimte in scenario-modus zit (>=1 slot gevuld),
- of de grafiek-zone gesplitst moet zijn,
- welke slot CM/PM-inhoud heeft of placeholder toont.
"""
from __future__ import annotations

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
    SPLIT_HORIZONTAL,
    SPLIT_NONE,
    SPLIT_VERTICAL,
    compute_split_layout,
)


def _state_with(keys: tuple[str, ...]) -> ScenarioSlotState:
    state = ScenarioSlotState()
    for k in keys:
        state.put(k, run_result=object(), project_snapshot=object())
    return state


def test_no_split_when_no_slots_filled():
    state = ScenarioSlotState()
    for mode in (MODE_BIJDRAGEN, MODE_LCC, MODE_FM_DETAIL):
        layout = compute_split_layout(state, mode)
        assert layout.orientation == SPLIT_NONE
        assert layout.cm_slot is None
        assert layout.pm_slot is None
        assert layout.scenario_mode is False


def test_filled_scenario_slots_do_not_enable_split_slice29():
    """Slice 29 #06 — legacy slots blijven in sessie, maar UI is altijd single-run."""
    state = _state_with((SCENARIO_KEY_CM, SCENARIO_KEY_PM))
    for mode in (MODE_BIJDRAGEN, MODE_LCC, MODE_FM_DETAIL):
        layout = compute_split_layout(state, mode)
        assert layout.orientation == SPLIT_NONE
        assert layout.scenario_mode is False
        assert layout.cm_slot is None
        assert layout.pm_slot is None
