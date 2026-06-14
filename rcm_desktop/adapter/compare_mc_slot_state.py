"""In-memory MC compare slots for Run A/B in Monte Carlo mode (slice 98)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A, COMPARE_SLOT_B
from rcm_desktop.adapter.simulation_engine_service import MCRunResult

_ALLOWED_KEYS = frozenset({COMPARE_SLOT_A, COMPARE_SLOT_B})


@dataclass(frozen=True)
class CompareMcSlotSnapshot:
    mc_run: MCRunResult
    label: str


class CompareMcSlotState:
    def __init__(self) -> None:
        self._slots: dict[str, CompareMcSlotSnapshot] = {}
        self._listeners: list[Callable[[], None]] = []

    def get(self, key: str) -> CompareMcSlotSnapshot | None:
        return self._slots.get(key)

    def put(self, key: str, snapshot: CompareMcSlotSnapshot) -> None:
        if key not in _ALLOWED_KEYS:
            raise ValueError(f"Onbekende MC compare-slot: {key!r}")
        self._slots[key] = snapshot
        self._emit()

    def has(self, key: str) -> bool:
        return key in self._slots

    def clear_all(self) -> None:
        self._slots.clear()
        self._emit()

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def _emit(self) -> None:
        for listener in self._listeners:
            listener()
