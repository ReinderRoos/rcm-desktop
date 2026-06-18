"""Read-only resultaten-tab voor FM-editor (slice 59.5)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import FMResult, PMTask, RCMProject

from rcm_desktop.adapter.calendar_year import calendar_year_for_horizon_index
from rcm_desktop.adapter.ltap_execution_schedule import ltap_executions_by_year


@dataclass(frozen=True)
class FmEditorPmResultRow:
    pm_id: str
    taak_type: str
    interval_jaar: float
    task_group_id: str
    first_execution_calendar_year: int | None


@dataclass(frozen=True)
class FmEditorResultsView:
    has_results: bool
    expected_failures: float
    total_downtime_hr: float
    pm_cost_eur: float
    cm_cost_eur: float
    total_cost_eur: float
    pm_type_counts: tuple[tuple[str, int], ...]
    pm_rows: tuple[FmEditorPmResultRow, ...]


def _taak_type_value(task: PMTask) -> str:
    raw = task.taak_type
    if hasattr(raw, "value"):
        return str(raw.value)
    return str(raw)


def _first_execution_calendar_year(project: RCMProject, task: PMTask) -> int | None:
    schedule = ltap_executions_by_year(
        task,
        lifecycle_years=float(project.config.lifecycle_years),
        anchor_year=0.0,
    )
    if not schedule:
        return None
    first_horizon = min(schedule.keys())
    return calendar_year_for_horizon_index(int(project.config.modeljaar), first_horizon)


def build_editor_results_view(
    project: RCMProject,
    fm_id: str,
    fmr: FMResult | None,
) -> FmEditorResultsView:
    pm_tasks = [
        task for task in project.pm_tasks.values() if task.fm_id == fm_id
    ]
    type_counts: dict[str, int] = {}
    for task in pm_tasks:
        tt = _taak_type_value(task)
        type_counts[tt] = type_counts.get(tt, 0) + 1
    pm_rows = tuple(
        FmEditorPmResultRow(
            pm_id=task.pm_id,
            taak_type=_taak_type_value(task),
            interval_jaar=float(task.interval_jaar),
            task_group_id=str(task.task_group_id or ""),
            first_execution_calendar_year=_first_execution_calendar_year(project, task),
        )
        for task in sorted(pm_tasks, key=lambda t: t.pm_id)
    )

    if fmr is None:
        return FmEditorResultsView(
            has_results=False,
            expected_failures=0.0,
            total_downtime_hr=0.0,
            pm_cost_eur=0.0,
            cm_cost_eur=0.0,
            total_cost_eur=0.0,
            pm_type_counts=tuple(sorted(type_counts.items())),
            pm_rows=pm_rows,
        )
    return FmEditorResultsView(
        has_results=True,
        expected_failures=float(fmr.expected_failures),
        total_downtime_hr=float(fmr.expected_total_downtime_hr),
        pm_cost_eur=float(fmr.pm_cost_eur),
        cm_cost_eur=float(fmr.expected_cm_cost_eur),
        total_cost_eur=float(fmr.total_cost_eur),
        pm_type_counts=tuple(sorted(type_counts.items())),
        pm_rows=pm_rows,
    )
