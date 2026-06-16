"""Scenario-kleur en compare-chrome helpers (slice 102)."""

from __future__ import annotations

from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A
from rcm_desktop.theme.dp_tokens import DP_SCENARIO_1, DP_SCENARIO_2


def scenario_color_hex(slot_key: str) -> str:
    """Presentatiekleur voor scenario 1 (slot A) of scenario 2 (slot B)."""
    if slot_key == COMPARE_SLOT_A:
        return DP_SCENARIO_1
    return DP_SCENARIO_2


def compare_header_stylesheet(slot_key: str) -> str:
    color = scenario_color_hex(slot_key)
    return f"color: {color}; font-weight: 600;"
