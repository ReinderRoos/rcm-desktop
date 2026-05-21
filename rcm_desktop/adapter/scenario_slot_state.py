"""In-memory CM/PM scenario run slots (legacy; werkruimte is single-run since slice 29)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

SCENARIO_KEY_CM = "cm"
SCENARIO_KEY_PM = "pm"

_ALLOWED_KEYS = frozenset({SCENARIO_KEY_CM, SCENARIO_KEY_PM})


@dataclass
class ScenarioSlot:
    run_result: Any
    project_snapshot: Any | None = None


class ScenarioSlotState:
    def __init__(self) -> None:
        self._slots: dict[str, ScenarioSlot] = {}
        self._last_run_key: str | None = None
        self._listeners: list[Callable[[], None]] = []

    def get(self, key: str) -> ScenarioSlot | None:
        return self._slots.get(key)

    def put(
        self,
        key: str,
        run_result: Any = None,
        *,
        project_snapshot: Any | None = None,
    ) -> None:
        if key not in _ALLOWED_KEYS:
            raise ValueError(f"Onbekende scenario-key: {key!r}")
        self._slots[key] = ScenarioSlot(
            run_result=run_result,
            project_snapshot=project_snapshot,
        )
        self._last_run_key = key
        self._emit()

    def last_run_key(self) -> str | None:
        return self._last_run_key

    def clear_all(self) -> None:
        self._slots.clear()
        self._last_run_key = None
        self._emit()

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def _emit(self) -> None:
        for listener in self._listeners:
            listener()
