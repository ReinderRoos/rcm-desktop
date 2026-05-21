"""Materialiseer tijdelijk run-project uit planning-overlay (slice 29)."""

from __future__ import annotations

from rcm_core.models import RCMProject

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState


def materialize_project_for_overlay(
    project: RCMProject,
    overlay: PlanningOverlayState,
) -> RCMProject:
    """Clone project zonder passieve PM-taken; origineel ongewijzigd."""
    disabled = overlay.disabled_pm_ids
    if not disabled:
        return project
    clone = RCMProject.from_dict(project.to_dict())
    allowed = {pm_id for pm_id in clone.pm_tasks if pm_id not in disabled}
    clone.pm_tasks = {pm_id: task for pm_id, task in clone.pm_tasks.items() if pm_id in allowed}
    clone.pm_effect_links = {
        link_id: link
        for link_id, link in clone.pm_effect_links.items()
        if link.pm_id in allowed
    }
    return clone
