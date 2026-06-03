from __future__ import annotations

import pytest

from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    COMPARE_SLOT_B,
    CompareSlotSnapshot,
    CompareSlotState,
    compare_slot_to_render_index,
    resolve_overlay_for_seed,
)
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.run_service import RunMetrics, RunResult


def _run(tag: str = "r") -> RunResult:
    return RunResult(
        status="done",
        summary=tag,
        metrics=RunMetrics(
            fm_result_count=0,
            total_lifecycle_faalmomenten=0.0,
            total_cost_eur=0.0,
        ),
    )


def test_empty_compare_slots():
    state = CompareSlotState()

    assert state.get(COMPARE_SLOT_A) is None
    assert state.get(COMPARE_SLOT_B) is None
    assert not state.has(COMPARE_SLOT_A)
    assert not state.both_filled()
    assert state.last_slot_key() is None


def test_put_and_get_snapshot():
    state = CompareSlotState()
    snap = CompareSlotSnapshot.from_motor_run(
        run_result=_run("a"),
        presentation=None,
        scenario_key=None,
        overlay_at_run=PlanningOverlayState.inactive(),
        label="A — project",
    )

    state.put(COMPARE_SLOT_A, snap)

    got = state.get(COMPARE_SLOT_A)
    assert got is snap
    assert state.has(COMPARE_SLOT_A)
    assert state.last_slot_key() == COMPARE_SLOT_A


def test_both_filled_requires_a_and_b():
    state = CompareSlotState()
    overlay = PlanningOverlayState.inactive()

    state.put(
        COMPARE_SLOT_A,
        CompareSlotSnapshot.from_motor_run(
            run_result=_run("a"),
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay,
            label="A",
        ),
    )
    assert not state.both_filled()

    state.put(
        COMPARE_SLOT_B,
        CompareSlotSnapshot.from_motor_run(
            run_result=_run("b"),
            presentation=None,
            scenario_key="pm",
            overlay_at_run=overlay,
            label="B",
        ),
    )
    assert state.both_filled()
    assert state.last_slot_key() == COMPARE_SLOT_B


def test_clear_all_empties_slots():
    state = CompareSlotState()
    overlay = PlanningOverlayState.inactive()
    state.put(
        COMPARE_SLOT_A,
        CompareSlotSnapshot.from_motor_run(
            run_result=_run("a"),
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay,
            label="A",
        ),
    )
    state.put(
        COMPARE_SLOT_B,
        CompareSlotSnapshot.from_motor_run(
            run_result=_run("b"),
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay,
            label="B",
        ),
    )

    state.clear_all()

    assert state.get(COMPARE_SLOT_A) is None
    assert state.last_slot_key() is None


def test_seed_from_last_run_without_motor():
    state = CompareSlotState()
    overlay = PlanningOverlayState.inactive()
    run = _run("seed")

    state.seed_from_last_run(
        COMPARE_SLOT_A,
        run_result=run,
        presentation=None,
        scenario_key="cm",
        overlay_at_run=overlay,
        label="A — CM",
    )

    snap = state.get(COMPARE_SLOT_A)
    assert snap is not None
    assert snap.run_result is run
    assert snap.scenario_key == "cm"


def test_resolve_overlay_for_seed_preserves_frozen_overlay_when_same_run():
    inactive = PlanningOverlayState.inactive()
    disabled = PlanningOverlayState(
        active=True,
        anchor_years=(),
        disabled_pm_ids=frozenset({"pm-1"}),
    )
    run = _run("same")
    existing = CompareSlotSnapshot.from_motor_run(
        run_result=run,
        presentation=None,
        scenario_key=None,
        overlay_at_run=disabled,
        label="B — passief",
    )

    resolved = resolve_overlay_for_seed(
        existing,
        proposed_overlay=inactive,
        run_result=run,
    )

    assert resolved is disabled


def test_seed_from_last_run_preserves_overlay_when_reseeding_same_run():
    inactive = PlanningOverlayState.inactive()
    disabled = PlanningOverlayState(
        active=True,
        anchor_years=(),
        disabled_pm_ids=frozenset({"pm-1"}),
    )
    run = _run("same")
    state = CompareSlotState()
    state.put(
        COMPARE_SLOT_B,
        CompareSlotSnapshot.from_motor_run(
            run_result=run,
            presentation=None,
            scenario_key=None,
            overlay_at_run=disabled,
            label="B — passief",
        ),
    )

    state.seed_from_last_run(
        COMPARE_SLOT_B,
        run_result=run,
        overlay_at_run=inactive,
        label="B — live",
    )

    snap = state.get(COMPARE_SLOT_B)
    assert snap is not None
    assert snap.overlay_at_run is disabled
    assert snap.label == "B — live"


def test_compare_slot_to_render_index_maps_a_and_b():
    from rcm_desktop.adapter.workspace_render_index import SLOT_A, SLOT_B

    assert compare_slot_to_render_index(COMPARE_SLOT_A) == SLOT_A
    assert compare_slot_to_render_index(COMPARE_SLOT_B) == SLOT_B

    with pytest.raises(ValueError):
        compare_slot_to_render_index("C")


def test_put_rejects_unknown_slot_key():
    state = CompareSlotState()
    overlay = PlanningOverlayState.inactive()
    snap = CompareSlotSnapshot.from_motor_run(
        run_result=_run("x"),
        presentation=None,
        scenario_key=None,
        overlay_at_run=overlay,
        label="X",
    )

    with pytest.raises(ValueError):
        state.put("C", snap)


def test_subscribe_notified_on_put_and_clear():
    state = CompareSlotState()
    seen: list[str | None] = []
    state.subscribe(lambda: seen.append(state.last_slot_key()))
    overlay = PlanningOverlayState.inactive()
    snap = CompareSlotSnapshot.from_motor_run(
        run_result=_run("a"),
        presentation=None,
        scenario_key=None,
        overlay_at_run=overlay,
        label="A",
    )

    state.put(COMPARE_SLOT_A, snap)
    state.clear_all()

    assert seen == [COMPARE_SLOT_A, None]
