"""Meekoppelkansen discovery — PBS-locatiegroepen (slice 40/55, ADR-0005)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import RCMProject, TaskType

from rcm_desktop.adapter.pbs_path_label_service import path_label
from rcm_desktop.adapter.result_filter_service import collect_pbs_subtree_ids


@dataclass(frozen=True)
class MeekoppelRevTask:
    pm_id: str
    pbs_id: str
    due_jaar: int


def bundling_pbs_id(project: RCMProject, fm_pbs_id: str) -> str:
    """Parent van FM-knoop als die in het model staat; anders de leaf zelf."""
    item = project.pbs_items.get(fm_pbs_id)
    if item is None:
        return fm_pbs_id
    parent = item.parent_pbs_id
    if parent and parent in project.pbs_items:
        return parent
    return fm_pbs_id


@dataclass(frozen=True)
class MeekoppelLocationGroup:
    """REV-taken op één bundelsleutel (parent of leaf-fallback) binnen het venster."""

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
        leaf_pbs_id = fm.pbs_id
        if leaf_pbs_id not in project.pbs_items:
            continue
        due = int(round(task.interval_jaar))
        bundle_key = bundling_pbs_id(project, leaf_pbs_id)
        by_pbs.setdefault(bundle_key, []).append(
            MeekoppelRevTask(pm_id=task.pm_id, pbs_id=leaf_pbs_id, due_jaar=due)
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


def covered_pbs_for_selection(
    project: RCMProject,
    selected_pbs_ids: frozenset[str],
) -> frozenset[str]:
    covered: set[str] = set()
    for pbs_id in selected_pbs_ids:
        if pbs_id not in project.pbs_items:
            continue
        covered.update(collect_pbs_subtree_ids(project, pbs_id))
    return frozenset(covered)


def collect_rev_tasks_for_pbs_selection(
    project: RCMProject,
    selected_pbs_ids: frozenset[str],
) -> tuple[MeekoppelRevTask, ...]:
    """Alle REV-taken onder geselecteerde PBS-knooppunten (subtree per knoop, dedupe op pm_id)."""
    if not selected_pbs_ids:
        return ()

    covered_pbs = covered_pbs_for_selection(project, selected_pbs_ids)
    if not covered_pbs:
        return ()

    seen_pm: set[str] = set()
    tasks: list[MeekoppelRevTask] = []
    for task in project.pm_tasks.values():
        if task.taak_type != TaskType.REV:
            continue
        if task.interval_jaar <= 0:
            continue
        fm = project.faalwijzes.get(task.fm_id)
        if fm is None or fm.pbs_id not in covered_pbs:
            continue
        if fm.pbs_id not in project.pbs_items:
            continue
        if task.pm_id in seen_pm:
            continue
        seen_pm.add(task.pm_id)
        due = int(round(task.interval_jaar))
        tasks.append(
            MeekoppelRevTask(pm_id=task.pm_id, pbs_id=fm.pbs_id, due_jaar=due)
        )
    return tuple(sorted(tasks, key=lambda t: (t.due_jaar, t.pm_id)))


def pbs_selection_path_label(project: RCMProject, selected_pbs_ids: frozenset[str]) -> str:
    if not selected_pbs_ids:
        return ""
    if len(selected_pbs_ids) == 1:
        return path_label(project, next(iter(selected_pbs_ids)))
    labels = [path_label(project, pid) for pid in sorted(selected_pbs_ids)]
    head = "; ".join(labels[:3])
    if len(labels) > 3:
        head = f"{head}; …"
    return f"{len(selected_pbs_ids)} onderdelen: {head}"

