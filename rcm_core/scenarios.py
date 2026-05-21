"""CM/PM scenario task filtering (slice 24, legacy compare path)."""

from __future__ import annotations

from rcm_core.models import RCMProject, TaskType

SCENARIO_CM = "CM"
SCENARIO_PM = "PM"

_ALLOWED_CM = frozenset({SCENARIO_CM, SCENARIO_PM})


def pm_tasks_for_scenario(project: RCMProject, scenario: str) -> frozenset[str]:
    """Return pm_ids included in the scenario materialization."""
    if scenario == SCENARIO_PM:
        return frozenset(project.pm_tasks.keys())
    if scenario != SCENARIO_CM:
        raise ValueError(f"Onbekend scenario: {scenario!r}")
    allowed: set[str] = set()
    for pm_id, task in project.pm_tasks.items():
        if task.taak_type == TaskType.SVO or task.is_wettelijk_verplicht:
            allowed.add(pm_id)
            continue
        fm = project.faalwijzes.get(task.fm_id)
        if fm is not None and not fm.is_evident and task.taak_type in (
            TaskType.IN,
            TaskType.TST,
        ):
            allowed.add(pm_id)
    return frozenset(allowed)
