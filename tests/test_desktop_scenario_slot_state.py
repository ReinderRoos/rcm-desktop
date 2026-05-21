from __future__ import annotations

import pytest

from rcm_desktop.adapter.scenario_slot_state import (
    SCENARIO_KEY_CM,
    SCENARIO_KEY_PM,
    ScenarioSlot,
    ScenarioSlotState,
)


class _FakeRun:
    def __init__(self, summary: str) -> None:
        self.summary = summary


def test_empty_state_has_no_slots_and_no_last_run_key():
    state = ScenarioSlotState()

    assert state.get(SCENARIO_KEY_CM) is None
    assert state.get(SCENARIO_KEY_PM) is None
    assert state.last_run_key() is None


def test_put_stores_slot_and_updates_last_run_key():
    state = ScenarioSlotState()
    rr_cm = _FakeRun("cm")

    state.put(SCENARIO_KEY_CM, rr_cm, project_snapshot=None)

    slot = state.get(SCENARIO_KEY_CM)
    assert isinstance(slot, ScenarioSlot)
    assert slot.run_result is rr_cm
    assert state.last_run_key() == SCENARIO_KEY_CM


def test_put_replaces_existing_slot_with_same_key():
    state = ScenarioSlotState()
    state.put(SCENARIO_KEY_CM, _FakeRun("first"), project_snapshot=None)

    second = _FakeRun("second")
    state.put(SCENARIO_KEY_CM, second, project_snapshot=None)

    assert state.get(SCENARIO_KEY_CM).run_result is second


def test_last_run_key_tracks_most_recent_put():
    state = ScenarioSlotState()
    state.put(SCENARIO_KEY_CM, _FakeRun("cm"), project_snapshot=None)
    state.put(SCENARIO_KEY_PM, _FakeRun("pm"), project_snapshot=None)

    assert state.last_run_key() == SCENARIO_KEY_PM


def test_clear_all_empties_state_and_drops_last_run_key():
    state = ScenarioSlotState()
    state.put(SCENARIO_KEY_CM, _FakeRun("cm"), project_snapshot=None)
    state.put(SCENARIO_KEY_PM, _FakeRun("pm"), project_snapshot=None)

    state.clear_all()

    assert state.get(SCENARIO_KEY_CM) is None
    assert state.get(SCENARIO_KEY_PM) is None
    assert state.last_run_key() is None


def test_put_rejects_unknown_scenario_key():
    state = ScenarioSlotState()

    with pytest.raises(ValueError):
        state.put("OPTIMIZED-but-not-yet-supported", _FakeRun("x"), project_snapshot=None)


def test_subscribe_listener_is_called_on_put_and_clear():
    state = ScenarioSlotState()
    seen: list = []
    state.subscribe(lambda: seen.append(state.last_run_key()))

    state.put(SCENARIO_KEY_CM, _FakeRun("cm"), project_snapshot=None)
    state.clear_all()

    assert seen == [SCENARIO_KEY_CM, None]
