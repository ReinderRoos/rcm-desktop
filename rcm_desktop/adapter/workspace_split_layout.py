"""Qt-vrije split-layout-orchestrator voor de resultatenwerkruimte.

Historisch: CM/PM-scenario-slots bepaalden een gesplitste grafiekzone. Sinds
slice 29 #06 retourneert :func:`compute_split_layout` altijd single-run layout;
what-if + ``last_run`` is SSOT in de werkruimte.

Bewust geen Qt-imports zodat deze module in unit-tests gebruikt kan worden
zonder een actieve `QApplication`.
"""
from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop.adapter.compare_split_layout_service import (
    SPLIT_HORIZONTAL,
    SPLIT_NONE,
    SPLIT_VERTICAL,
)
from rcm_desktop.adapter.scenario_slot_state import (
    ScenarioSlot,
    ScenarioSlotState,
)


@dataclass(frozen=True)
class SplitSlot:
    """Eén kant van de gesplitste weergave (CM óf PM)."""

    scenario_key: str
    slot: ScenarioSlot | None
    placeholder: bool


@dataclass(frozen=True)
class SplitLayout:
    """Resultaat van :func:`compute_split_layout`."""

    orientation: str
    scenario_mode: bool
    cm_slot: SplitSlot | None
    pm_slot: SplitSlot | None


def compute_split_layout(
    slots: ScenarioSlotState,
    mode: str,
) -> SplitLayout:
    """Single-run SSOT voor de werkruimte (slice 29 #06).

    Legacy :class:`ScenarioSlotState` kan nog CM/PM-runs bevatten (bijv. tests of
    toekomstige opruim), maar de resultatenwerkruimte splitst niet meer op
    scenario-slots. What-if + ``last_run`` is het standaardpad.
    """
    del slots, mode
    return SplitLayout(
        orientation=SPLIT_NONE,
        scenario_mode=False,
        cm_slot=None,
        pm_slot=None,
    )
