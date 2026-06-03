"""Post-run orchestration for A/B compare slots (slice 56)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop.adapter.compare_run_service import CompareRunOutcome
from rcm_desktop.adapter.compare_slot_state import (
    CompareSlotSnapshot,
    CompareSlotState,
    compare_slot_to_render_index,
)
from rcm_desktop.adapter.run_service import RunResult


@dataclass(frozen=True)
class SlotRunCompletePlan:
    slot_key: str
    snapshot: CompareSlotSnapshot
    render_slot_key: str
    update_last_run: bool


class CompareWorkspaceController:
    @staticmethod
    def plan_after_slot_run(
        slot_key: str,
        outcome: CompareRunOutcome,
        *,
        previous_snapshot: CompareSlotSnapshot | None,
    ) -> SlotRunCompletePlan | None:
        if outcome.status != "done" or outcome.snapshot is None:
            return None
        render_key = compare_slot_to_render_index(slot_key)
        return SlotRunCompletePlan(
            slot_key=slot_key,
            snapshot=outcome.snapshot,
            render_slot_key=render_key,
            update_last_run=True,
        )

    @staticmethod
    def apply_slot_run(
        slots: CompareSlotState,
        plan: SlotRunCompletePlan,
    ) -> RunResult:
        slots.put(plan.slot_key, plan.snapshot)
        return plan.snapshot.run_result

    @staticmethod
    def should_keep_previous_slot_on_error(
        slot_key: str,
        outcome: CompareRunOutcome,
        *,
        previous: CompareSlotSnapshot | None,
    ) -> bool:
        if outcome.status == "done":
            return False
        return previous is not None
