"""CM-beleid preset voor planning what-if (slice 29)."""
from __future__ import annotations

from rcm_core.models import RCMProject

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState


def apply_cm_policy_preset(
    overlay: PlanningOverlayState,
    project: RCMProject,
) -> PlanningOverlayState:
    """Zet alle PM-taken passief (CM-scenario in overlay)."""
    return PlanningOverlayState(
        active=True,
        anchor_years=overlay.anchor_years,
        disabled_pm_ids=frozenset(project.pm_tasks),
    )
