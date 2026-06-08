"""Pre-run configuration for A/B slot runs (slice 56)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState


@dataclass(frozen=True)
class CompareRunConfig:
    scenario_key: str | None  # None = project-as-loaded, "cm", "pm"
    planning_overlay: PlanningOverlayState
    force_recompute: bool = False
