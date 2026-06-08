"""Bundle preview insight — scope, drivers, per-task years (slice 54, Qt-vrij)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rcm_core.models import RCMProject

from rcm_desktop.adapter.meekoppel_apply_service import (
    MeekoppelAnchor,
    MeekoppelLocationPreview,
    effective_due_year,
    preview_meekoppel_rev_tasks,
)
from rcm_desktop.adapter.meekoppel_display_service import pm_task_label
from rcm_desktop.adapter.meekoppelkansen_discovery_service import (
    MeekoppelLocationGroup,
    MeekoppelRevTask,
    collect_rev_tasks_for_pbs_selection,
    pbs_selection_path_label,
)

def _pbs_ids_label(pbs_ids: frozenset[str]) -> str:
    return ", ".join(sorted(pbs_ids))

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.pm_task_policy import pm_shift_block_reason
from rcm_desktop.adapter.project_session import ProjectSession

BundleScopeKind = Literal["location_row", "pbs_selection"]


@dataclass(frozen=True)
class MeekoppelTargetDriver:
    pm_id: str
    task_label: str
    baseline_year: int
    effective_year: int


@dataclass(frozen=True)
class MeekoppelPreviewTaskRow:
    pm_id: str
    task_label: str
    baseline_year: int
    effective_year: int
    target_year: int
    delta_years: int
    is_target_driver: bool
    blocked_reason: str | None


@dataclass(frozen=True)
class MeekoppelBundleInsight:
    scope_kind: BundleScopeKind
    scope_label: str
    scope_task_count: int
    target_drivers: tuple[MeekoppelTargetDriver, ...]
    summary_lines: tuple[str, ...]
    task_rows: tuple[MeekoppelPreviewTaskRow, ...]


def resolve_default_scope_kind(
    *,
    selected_location_group: MeekoppelLocationGroup | None,
) -> BundleScopeKind:
    if selected_location_group is not None:
        return "location_row"
    return "pbs_selection"


def resolve_scope_bundle(
    session: ProjectSession,
    scope_kind: BundleScopeKind,
    *,
    pbs_ids: frozenset[str],
    location_group: MeekoppelLocationGroup | None,
) -> tuple[str, str, tuple[MeekoppelRevTask, ...]] | None:
    project = session.loaded.core()
    if scope_kind == "location_row":
        if location_group is None:
            return None
        label = f"{location_group.path_label} · {location_group.rev_count} REV"
        return (location_group.pbs_id, label, location_group.tasks)
    if not pbs_ids:
        return None
    tasks = collect_rev_tasks_for_pbs_selection(project, pbs_ids)
    if not tasks:
        return None
    label = f"{pbs_selection_path_label(project, pbs_ids)} · {len(tasks)} REV"
    return (_pbs_ids_label(pbs_ids), label, tasks)


def _target_driver_rows(
    project: RCMProject,
    overlay: PlanningOverlayState,
    tasks: tuple[MeekoppelRevTask, ...],
    target_year: int,
) -> tuple[MeekoppelTargetDriver, ...]:
    drivers: list[MeekoppelTargetDriver] = []
    for task in tasks:
        if pm_shift_block_reason(project.pm_tasks.get(task.pm_id)):
            continue
        eff = effective_due_year(project, overlay, task.pm_id)
        if eff != target_year:
            continue
        drivers.append(
            MeekoppelTargetDriver(
                pm_id=task.pm_id,
                task_label=pm_task_label(project, task.pm_id),
                baseline_year=int(task.due_jaar),
                effective_year=eff,
            )
        )
    drivers.sort(key=lambda d: d.task_label)
    return tuple(drivers)


def _determined_by_line(
    drivers: tuple[MeekoppelTargetDriver, ...],
    target_year: int,
) -> str:
    from rcm_desktop import messages

    if not drivers:
        return messages.WORKSPACE_MEEKOPPEL_PREVIEW_NO_MOVES
    if len(drivers) == 1:
        d = drivers[0]
        return messages.WORKSPACE_MEEKOPPEL_PREVIEW_DETERMINED_BY_ONE.format(
            label=d.task_label,
            baseline=d.baseline_year,
            effective=d.effective_year,
        )
    return messages.WORKSPACE_MEEKOPPEL_PREVIEW_DETERMINED_BY_MANY.format(
        count=len(drivers),
        year=target_year,
    )


def _build_task_rows(
    project: RCMProject,
    overlay: PlanningOverlayState,
    tasks: tuple[MeekoppelRevTask, ...],
    target_year: int,
) -> tuple[MeekoppelPreviewTaskRow, ...]:
    rows: list[MeekoppelPreviewTaskRow] = []
    for task in tasks:
        blocked = pm_shift_block_reason(project.pm_tasks.get(task.pm_id))
        eff = effective_due_year(project, overlay, task.pm_id)
        is_driver = blocked is None and eff == target_year and target_year > 0
        rows.append(
            MeekoppelPreviewTaskRow(
                pm_id=task.pm_id,
                task_label=pm_task_label(project, task.pm_id),
                baseline_year=int(task.due_jaar),
                effective_year=eff,
                target_year=target_year,
                delta_years=int(target_year - eff) if target_year > 0 else 0,
                is_target_driver=is_driver,
                blocked_reason=blocked,
            )
        )

    def sort_key(row: MeekoppelPreviewTaskRow) -> tuple:
        return (
            0 if row.is_target_driver else 1,
            -abs(row.delta_years),
            row.task_label,
        )

    return tuple(sorted(rows, key=sort_key))


def build_bundle_insight(
    project: RCMProject,
    overlay: PlanningOverlayState,
    *,
    scope_kind: BundleScopeKind,
    scope_label: str,
    tasks: tuple[MeekoppelRevTask, ...],
    preview: MeekoppelLocationPreview,
) -> MeekoppelBundleInsight:
    from rcm_desktop import messages

    target = preview.target_year
    drivers = _target_driver_rows(project, overlay, tasks, target)
    scope_line = messages.WORKSPACE_MEEKOPPEL_PREVIEW_SCOPE_LINE.format(
        scope_label=scope_label,
        count=len(tasks),
    )
    determined = _determined_by_line(drivers, target)
    return MeekoppelBundleInsight(
        scope_kind=scope_kind,
        scope_label=scope_label,
        scope_task_count=len(tasks),
        target_drivers=drivers,
        summary_lines=(scope_line, determined),
        task_rows=_build_task_rows(project, overlay, tasks, target),
    )


def preview_meekoppel_with_insight(
    session: ProjectSession,
    overlay: PlanningOverlayState,
    *,
    pbs_ids: frozenset[str],
    anchor: MeekoppelAnchor,
    scope_kind: BundleScopeKind | None = None,
    location_group: MeekoppelLocationGroup | None = None,
) -> MeekoppelLocationPreview:
    kind = scope_kind or resolve_default_scope_kind(
        selected_location_group=location_group
    )
    bundle = resolve_scope_bundle(
        session,
        kind,
        pbs_ids=pbs_ids,
        location_group=location_group,
    )
    if bundle is None:
        from rcm_desktop import messages

        return MeekoppelLocationPreview(
            pbs_id="",
            path_label="",
            target_year=0,
            moves=(),
            blocked_reason=messages.WORKSPACE_MEEKOPPEL_SELECT_PBS,
        )
    pbs_id_label, scope_label, tasks = bundle
    project = session.loaded.core()
    preview = preview_meekoppel_rev_tasks(
        project,
        overlay,
        pbs_id_label=pbs_id_label,
        path_label=scope_label,
        tasks=tasks,
        anchor=anchor,
    )
    if preview.blocked_reason:
        return preview
    insight = build_bundle_insight(
        project,
        overlay,
        scope_kind=kind,
        scope_label=scope_label,
        tasks=tasks,
        preview=preview,
    )
    return MeekoppelLocationPreview(
        pbs_id=preview.pbs_id,
        path_label=preview.path_label,
        target_year=preview.target_year,
        moves=preview.moves,
        blocked_reason=preview.blocked_reason,
        total_task_count=preview.total_task_count,
        skipped=preview.skipped,
        bundle_insight=insight,
    )
