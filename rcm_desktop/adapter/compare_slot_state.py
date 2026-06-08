"""In-memory A/B compare slots for the resultatenwerkruimte (slice 56)."""



from __future__ import annotations



from dataclasses import dataclass

from typing import Callable



from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState

from rcm_desktop.adapter.presentation_cache_service import PresentationProjectTotal

from rcm_desktop.adapter.run_service import RunResult

from rcm_desktop.adapter.workspace_render_index import SLOT_A, SLOT_B



COMPARE_SLOT_A = "A"

COMPARE_SLOT_B = "B"



_ALLOWED_KEYS = frozenset({COMPARE_SLOT_A, COMPARE_SLOT_B})





def compare_slot_to_render_index(slot_key: str) -> str:

    if slot_key == COMPARE_SLOT_A:

        return SLOT_A

    if slot_key == COMPARE_SLOT_B:

        return SLOT_B

    raise ValueError(f"Onbekende compare-slot: {slot_key!r}")





def resolve_overlay_for_seed(

    existing: CompareSlotSnapshot | None,

    *,

    proposed_overlay: PlanningOverlayState,

    run_result: RunResult,

) -> PlanningOverlayState:

    """Behoud bevroren overlay bij her-seed van dezelfde motorrun."""

    if existing is not None and existing.run_result is run_result:

        return existing.overlay_at_run

    return proposed_overlay





@dataclass(frozen=True)

class CompareSlotSnapshot:

    """Bevroren motorrun + overlay zoals bij run/seed vastgelegd."""



    run_result: RunResult

    presentation: PresentationProjectTotal | None

    scenario_key: str | None  # None | "cm" | "pm"

    overlay_at_run: PlanningOverlayState

    label: str



    @classmethod

    def from_motor_run(

        cls,

        *,

        run_result: RunResult,

        presentation: PresentationProjectTotal | None,

        scenario_key: str | None,

        overlay_at_run: PlanningOverlayState,

        label: str,

    ) -> CompareSlotSnapshot:

        if run_result.status != "done":

            raise ValueError("Alleen voltooide motorruns kunnen in een compare-slot.")

        return cls(

            run_result=run_result,

            presentation=presentation,

            scenario_key=scenario_key,

            overlay_at_run=overlay_at_run,

            label=label,

        )





class CompareSlotState:

    def __init__(self) -> None:

        self._slots: dict[str, CompareSlotSnapshot] = {}

        self._last_slot_key: str | None = None

        self._listeners: list[Callable[[], None]] = []



    def get(self, key: str) -> CompareSlotSnapshot | None:

        return self._slots.get(key)



    def put(self, key: str, snapshot: CompareSlotSnapshot) -> None:

        if key not in _ALLOWED_KEYS:

            raise ValueError(f"Onbekende compare-slot: {key!r}")

        self._slots[key] = snapshot

        self._last_slot_key = key

        self._emit()



    def clear(self, key: str) -> None:

        if key in self._slots:

            del self._slots[key]

        if self._last_slot_key == key:

            self._last_slot_key = (

                COMPARE_SLOT_B

                if COMPARE_SLOT_A in self._slots

                else COMPARE_SLOT_A

                if COMPARE_SLOT_B in self._slots

                else None

            )

        self._emit()



    def clear_all(self) -> None:

        self._slots.clear()

        self._last_slot_key = None

        self._emit()



    def has(self, key: str) -> bool:

        return key in self._slots



    def both_filled(self) -> bool:

        return COMPARE_SLOT_A in self._slots and COMPARE_SLOT_B in self._slots



    def last_slot_key(self) -> str | None:

        return self._last_slot_key



    def seed_from_last_run(

        self,

        key: str,

        *,

        run_result: RunResult,

        presentation: PresentationProjectTotal | None = None,

        scenario_key: str | None = None,

        overlay_at_run: PlanningOverlayState | None = None,

        label: str,

    ) -> None:

        if key not in _ALLOWED_KEYS:

            raise ValueError(f"Onbekende compare-slot: {key!r}")

        proposed = overlay_at_run or PlanningOverlayState.inactive()

        overlay = resolve_overlay_for_seed(

            self.get(key),

            proposed_overlay=proposed,

            run_result=run_result,

        )

        self.put(

            key,

            CompareSlotSnapshot.from_motor_run(

                run_result=run_result,

                presentation=presentation,

                scenario_key=scenario_key,

                overlay_at_run=overlay,

                label=label,

            ),

        )



    def subscribe(self, listener: Callable[[], None]) -> None:

        self._listeners.append(listener)



    def _emit(self) -> None:

        for listener in self._listeners:

            listener()


