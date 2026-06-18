"""Scenario workflow state: freeze live run, scenario slots (slice 100 issue 04)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop.adapter.compare_slot_label import build_scenario_slot_label
from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    COMPARE_SLOT_B,
    CompareSlotSnapshot,
    CompareSlotState,
)
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.presentation_cache_service import PresentationProjectTotal
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.simulation_engine_service import MCRunResult
from rcm_desktop.adapter.simulation_job_service import RunMode

SCENARIO_1 = COMPARE_SLOT_A
SCENARIO_2 = COMPARE_SLOT_B


@dataclass(frozen=True)
class LiveRunSnapshot:
    run_mode: RunMode
    run_result: RunResult | None
    mc_run: MCRunResult | None
    overlay: PlanningOverlayState
    scenario_key: str | None
    presentation: PresentationProjectTotal | None


class ScenarioWorkflowService:
    def __init__(self, slots: CompareSlotState | None = None) -> None:
        self._slots = slots or CompareSlotState()
        self._variant_mode = False

    @property
    def slots(self) -> CompareSlotState:
        return self._slots

    @property
    def variant_mode(self) -> bool:
        return self._variant_mode

    def has_any_scenario(self) -> bool:
        return self.has(SCENARIO_1) or self.has(SCENARIO_2)

    def get_scenario_1(self) -> CompareSlotSnapshot | None:
        return self._slots.get(SCENARIO_1)

    def get_scenario_2(self) -> CompareSlotSnapshot | None:
        return self._slots.get(SCENARIO_2)

    def has(self, key: str) -> bool:
        return self._slots.has(key)

    def both_filled(self) -> bool:
        return self._slots.both_filled()

    def clear_all(self) -> None:
        self._slots.clear_all()
        self._variant_mode = False

    def enter_extra_scenario(self, live: LiveRunSnapshot) -> None:
        """Freeze live → scenario 1 (once) and open variant config for scenario 2."""
        if not self.has(SCENARIO_1):
            self.freeze_live_as_scenario_1(live)
        self._variant_mode = True

    def apply_variant_live_run(self, live: LiveRunSnapshot) -> None:
        """Successful Start analyse in variant-modus fills scenario 2."""
        self.put_scenario_2(live)

    def freeze_live_as_scenario_1(self, live: LiveRunSnapshot) -> None:
        self._put_scenario(SCENARIO_1, live)

    def put_scenario_2(self, live: LiveRunSnapshot) -> None:
        self._put_scenario(SCENARIO_2, live)

    def _put_scenario(self, slot_key: str, live: LiveRunSnapshot) -> None:
        label = build_scenario_slot_label(
            slot_key,
            run_mode=live.run_mode,
            scenario_key=live.scenario_key,
            overlay=live.overlay,
            mc_run=live.mc_run,
        )
        if live.run_mode is RunMode.MONTE_CARLO:
            if live.mc_run is None or live.run_result is None:
                raise ValueError("MC scenario vereist mc_run en P50 run_result.")
            snap = CompareSlotSnapshot.from_mc_run(
                mc_run=live.mc_run,
                run_result=live.run_result,
                presentation=live.presentation,
                scenario_key=live.scenario_key,
                overlay_at_run=live.overlay,
                label=label,
            )
        else:
            if live.run_result is None:
                raise ValueError("Analytisch scenario vereist run_result.")
            snap = CompareSlotSnapshot.from_motor_run(
                run_result=live.run_result,
                presentation=live.presentation,
                scenario_key=live.scenario_key,
                overlay_at_run=live.overlay,
                label=label,
                run_mode=RunMode.ANALYTICAL,
            )
        self._slots.put(slot_key, snap)
