"""Meekoppelkansen discovery — PBS-locatiegroepen (slice 40, ADR-0005)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import RCMProject, TaskType

from rcm_desktop.adapter.pbs_path_label_service import path_label


@dataclass(frozen=True)
class MeekoppelRevTask:
    pm_id: str
    pbs_id: str
    due_jaar: int


@dataclass(frozen=True)
class MeekoppelLocationGroup:
    """Alle REV-taken op één PBS-locatie met due-span binnen het tijdsvenster."""

    pbs_id: str
    path_label: str
    tasks: tuple[MeekoppelRevTask, ...]
    min_due_jaar: int
    max_due_jaar: int
    span_jaar: int

    @property
    def rev_count(self) -> int:
        return len(self.tasks)

    def due_range_label(self) -> str:
        if self.min_due_jaar == self.max_due_jaar:
            return str(self.min_due_jaar)
        return f"{self.min_due_jaar}–{self.max_due_jaar}"


def _collect_rev_by_pbs(project: RCMProject) -> dict[str, list[MeekoppelRevTask]]:
    by_pbs: dict[str, list[MeekoppelRevTask]] = {}
    for task in project.pm_tasks.values():
        if task.taak_type != TaskType.REV:
            continue
        if task.interval_jaar <= 0:
            continue
        fm = project.faalwijzes.get(task.fm_id)
        if fm is None:
            continue
        pbs_id = fm.pbs_id
        if pbs_id not in project.pbs_items:
            continue
        due = int(round(task.interval_jaar))
        by_pbs.setdefault(pbs_id, []).append(
            MeekoppelRevTask(pm_id=task.pm_id, pbs_id=pbs_id, due_jaar=due)
        )
    return by_pbs


def discover_meekoppel_locations(
    project: RCMProject,
    *,
    window_years: int = 2,
) -> tuple[MeekoppelLocationGroup, ...]:
    """REV-taken per PBS-locatie; groep als ≥2 taken en (max−min) due ≤ venster."""
    if window_years < 0:
        return ()

    out: list[MeekoppelLocationGroup] = []
    for pbs_id, raw in sorted(_collect_rev_by_pbs(project).items()):
        if len(raw) < 2:
            continue
        tasks = tuple(sorted(raw, key=lambda t: (t.due_jaar, t.pm_id)))
        min_due = tasks[0].due_jaar
        max_due = tasks[-1].due_jaar
        span = max_due - min_due
        if span > window_years:
            continue
        out.append(
            MeekoppelLocationGroup(
                pbs_id=pbs_id,
                path_label=path_label(project, pbs_id),
                tasks=tasks,
                min_due_jaar=min_due,
                max_due_jaar=max_due,
                span_jaar=span,
            )
        )
    return tuple(out)
