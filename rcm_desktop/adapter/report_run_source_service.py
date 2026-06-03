"""Bepaal welke runs in het rapport komen (slice 57)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    COMPARE_SLOT_B,
    CompareSlotSnapshot,
    CompareSlotState,
)
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.run_service import RunResult


@dataclass(frozen=True)
class ReportScenarioRun:
    key: str
    label: str
    run_result: RunResult
    overlay_at_run: PlanningOverlayState
    scenario_key: str | None


@dataclass(frozen=True)
class ReportRunBundle:
    mode: Literal["single", "compare"]
    scenarios: tuple[ReportScenarioRun, ...]


def _snapshot_to_scenario(key: str, snap: CompareSlotSnapshot) -> ReportScenarioRun:
    return ReportScenarioRun(
        key=key,
        label=snap.label,
        run_result=snap.run_result,
        overlay_at_run=snap.overlay_at_run,
        scenario_key=snap.scenario_key,
    )


def resolve_report_run_bundle(
    *,
    last_run: RunResult | None,
    compare_slots: CompareSlotState | None,
    live_overlay: PlanningOverlayState | None = None,
) -> ReportRunBundle | None:
    if compare_slots is not None and compare_slots.both_filled():
        a = compare_slots.get(COMPARE_SLOT_A)
        b = compare_slots.get(COMPARE_SLOT_B)
        if a is None or b is None:
            return None
        return ReportRunBundle(
            mode="compare",
            scenarios=(
                _snapshot_to_scenario(COMPARE_SLOT_A, a),
                _snapshot_to_scenario(COMPARE_SLOT_B, b),
            ),
        )
    if compare_slots is not None:
        snap = compare_slots.get(COMPARE_SLOT_A)
        if snap is not None and snap.run_result.status == "done":
            return ReportRunBundle(
                mode="single",
                scenarios=(_snapshot_to_scenario(COMPARE_SLOT_A, snap),),
            )
    if last_run is not None and last_run.status == "done":
        overlay = live_overlay or PlanningOverlayState.inactive()
        return ReportRunBundle(
            mode="single",
            scenarios=(
                ReportScenarioRun(
                    key="current",
                    label="Huidige analyse",
                    run_result=last_run,
                    overlay_at_run=overlay,
                    scenario_key=None,
                ),
            ),
        )
    return None
