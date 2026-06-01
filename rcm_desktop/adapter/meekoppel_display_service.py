"""Display helpers voor meekoppel-paneel (UX v2, Qt-vrij)."""

from __future__ import annotations

from rcm_core.models import RCMProject

from rcm_desktop.adapter.meekoppel_apply_service import MeekoppelShiftMove
from rcm_desktop.adapter.meekoppelkansen_discovery_service import MeekoppelLocationGroup


def due_calendar_year(modeljaar: int, due_jaar: int) -> int:
    """Kalenderjaar ≈ modeljaar + horizonindex (due-jaar)."""
    return int(modeljaar) + int(due_jaar)


def pm_task_label(project: RCMProject, pm_id: str, *, max_len: int = 80) -> str:
    task = project.pm_tasks.get(pm_id)
    if task is None:
        return pm_id
    label = (task.taak_omschrijving or "").strip()
    if not label:
        return pm_id
    if len(label) <= max_len:
        return label
    return label[: max_len - 1].rstrip() + "…"


def location_group_tooltip(project: RCMProject, group: MeekoppelLocationGroup) -> str:
    lines = [f"PBS-id: {group.pbs_id}", "REV-taken:"]
    for task in group.tasks:
        label = pm_task_label(project, task.pm_id)
        lines.append(f"  • {label} (jaar {task.due_jaar})")
    return "\n".join(lines)


def format_preview_move_line(
    project: RCMProject,
    modeljaar: int,
    move: MeekoppelShiftMove,
) -> str:
    from rcm_desktop import messages

    return messages.WORKSPACE_MEEKOPPEL_PREVIEW_MOVE_LINE.format(
        task_label=pm_task_label(project, move.pm_id),
        from_year=move.from_year,
        to_year=move.to_year,
        from_cal=due_calendar_year(modeljaar, move.from_year),
        to_cal=due_calendar_year(modeljaar, move.to_year),
        shift=move.shift_years,
    )
