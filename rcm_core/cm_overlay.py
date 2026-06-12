"""CM-overlay materialisatie uit AW-import (slice 67, Qt-vrij)."""

from __future__ import annotations

from rcm_core.models import RCMProject


def aw_disabled_pm_ids(project: RCMProject) -> frozenset[str]:
    """PM-taken uitgeschakeld in AW CM-scenario (Enabled=False bij import)."""
    raw = (project.import_settings or {}).get("aw_disabled_pm_ids") or []
    if not isinstance(raw, list):
        return frozenset()
    return frozenset(str(x) for x in raw if x)


def materialize_cm_overlay_project(project: RCMProject) -> RCMProject:
    """Clone zonder uitgeschakelde PM-taken — zelfde PM-set als ef_cm_overlay."""
    disabled = aw_disabled_pm_ids(project)
    if not disabled:
        return project
    clone = RCMProject.from_dict(project.to_dict())
    allowed = {pm_id for pm_id in clone.pm_tasks if pm_id not in disabled}
    clone.pm_tasks = {
        pm_id: task for pm_id, task in clone.pm_tasks.items() if pm_id in allowed
    }
    clone.pm_effect_links = {
        link_id: link
        for link_id, link in clone.pm_effect_links.items()
        if link.pm_id in allowed
    }
    return clone
