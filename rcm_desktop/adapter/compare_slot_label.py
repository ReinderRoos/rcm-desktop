"""Human-readable labels for A/B compare slots."""

from __future__ import annotations

from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A, COMPARE_SLOT_B
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState

_SCENARIO_LABELS = {
    None: "project",
    "cm": "CM",
    "pm": "PM",
}


def build_compare_slot_label(
    slot_key: str,
    *,
    scenario_key: str | None,
    overlay: PlanningOverlayState,
) -> str:
    scenario = _SCENARIO_LABELS.get(scenario_key, str(scenario_key))
    suffix = ""
    if overlay.active:
        n_disabled = len(overlay.disabled_pm_ids)
        if n_disabled:
            suffix = f", {n_disabled} PM passief"
        if overlay.anchor_years:
            suffix += f", {len(overlay.anchor_years)} verankerd"
    slot = "A" if slot_key == COMPARE_SLOT_A else "B"
    base = f"{slot} — {scenario}"
    return base + suffix if suffix else base


def build_mc_compare_slot_label(slot_key: str, *, seed: int) -> str:
    slot = "A" if slot_key == COMPARE_SLOT_A else "B"
    return f"{slot} — MC (seed {seed})"
