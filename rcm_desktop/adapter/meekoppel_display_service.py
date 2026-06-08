"""Display helpers voor meekoppel-paneel (UX v2, Qt-vrij)."""

from __future__ import annotations

from rcm_core.models import RCMProject

from rcm_desktop.adapter.meekoppel_apply_service import (
    MeekoppelLocationPreview,
    MeekoppelShiftMove,
    effective_due_year,
)
from rcm_desktop.adapter.meekoppelkansen_discovery_service import (
    MeekoppelLocationGroup,
    MeekoppelRevTask,
)
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState


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


def rev_task_tooltip_line(
    project: RCMProject,
    task: MeekoppelRevTask,
    *,
    overlay: PlanningOverlayState | None,
) -> str:
    from rcm_desktop import messages

    label = pm_task_label(project, task.pm_id)
    baseline = int(task.due_jaar)
    if overlay is not None and overlay.active:
        effective = effective_due_year(project, overlay, task.pm_id)
        return messages.WORKSPACE_MEEKOPPEL_TOOLTIP_TASK_BASELINE_EFFECTIVE.format(
            label=label,
            baseline=baseline,
            effective=effective,
        )
    return messages.WORKSPACE_MEEKOPPEL_TOOLTIP_TASK_BASELINE.format(
        label=label,
        baseline=baseline,
    )


def location_group_tooltip(
    project: RCMProject,
    group: MeekoppelLocationGroup,
    *,
    overlay: PlanningOverlayState | None = None,
) -> str:
    lines = [f"PBS-id: {group.pbs_id}", "REV-taken:"]
    for task in group.tasks:
        lines.append(rev_task_tooltip_line(project, task, overlay=overlay))
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


def format_preview_unchanged_line(
    project: RCMProject,
    modeljaar: int,
    pm_id: str,
    *,
    year: int,
) -> str:
    from rcm_desktop import messages

    return messages.WORKSPACE_MEEKOPPEL_PREVIEW_UNCHANGED_LINE.format(
        task_label=pm_task_label(project, pm_id),
        year=year,
        cal=due_calendar_year(modeljaar, year),
    )


def format_preview_skipped_line(project: RCMProject, pm_id: str, reason: str) -> str:
    from rcm_desktop import messages

    return messages.WORKSPACE_MEEKOPPEL_PREVIEW_SKIPPED_LINE.format(
        task_label=pm_task_label(project, pm_id),
        reason=reason,
    )


def format_meekoppel_preview_moves_text(
    project: RCMProject,
    overlay: PlanningOverlayState,
    modeljaar: int,
    preview: MeekoppelLocationPreview,
    tasks: tuple[MeekoppelRevTask, ...],
) -> str:
    """Alle REV-taken in de selectie: verschuiving, al op doel, of overgeslagen."""
    from rcm_desktop import messages

    if not tasks:
        return messages.WORKSPACE_MEEKOPPEL_PREVIEW_NO_MOVES

    move_by_pm = {move.pm_id: move for move in preview.moves}
    skipped_by_pm = dict(preview.skipped)
    lines: list[str] = []
    for task in sorted(tasks, key=lambda t: (t.due_jaar, t.pm_id)):
        if task.pm_id in skipped_by_pm:
            lines.append(
                format_preview_skipped_line(
                    project, task.pm_id, skipped_by_pm[task.pm_id]
                )
            )
            continue
        move = move_by_pm.get(task.pm_id)
        if move is not None:
            lines.append(format_preview_move_line(project, modeljaar, move))
            continue
        eff = effective_due_year(project, overlay, task.pm_id)
        lines.append(
            format_preview_unchanged_line(
                project, modeljaar, task.pm_id, year=eff
            )
        )
    return "\n".join(lines)
