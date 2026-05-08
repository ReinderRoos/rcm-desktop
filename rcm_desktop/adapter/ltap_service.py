from __future__ import annotations

from dataclasses import dataclass
import math

from rcm_core.models import PMTask, RCMProject, TaskType


@dataclass(frozen=True)
class LTAPTaskDetail:
    pm_id: str
    pm_label: str
    fm_id: str
    taak_type: str
    taak_omschrijving: str
    executions: int
    pm_cost_eur: float
    planned_downtime_hr: float
    anchor_year: float
    shiftable: bool


@dataclass(frozen=True)
class LTAPYearRow:
    year: int
    task_count: int
    pm_cost_eur: float
    planned_downtime_hr: float
    details: tuple[LTAPTaskDetail, ...]


@dataclass(frozen=True)
class LTAPView:
    years: tuple[LTAPYearRow, ...]
    total_task_count: int
    total_pm_cost_eur: float
    total_planned_downtime_hr: float


def build_ltap_view(
    project: RCMProject,
    *,
    overlay_anchor_years: dict[str, float] | None = None,
    taak_type_filter: str | None = None,
) -> LTAPView:
    lifecycle_years = float(project.config.lifecycle_years)
    max_year = max(0, math.ceil(lifecycle_years) - 1)
    by_year: dict[int, list[LTAPTaskDetail]] = {year: [] for year in range(max_year + 1)}

    for task in sorted(project.pm_tasks.values(), key=lambda item: item.pm_id):
        if taak_type_filter is not None and task.taak_type.value != taak_type_filter:
            continue
        anchor_year = float((overlay_anchor_years or {}).get(task.pm_id, 0.0))
        executions_by_year = _executions_by_year(task, lifecycle_years=lifecycle_years, anchor_year=anchor_year)
        for year, executions in executions_by_year.items():
            if executions <= 0:
                continue
            by_year[year].append(
                LTAPTaskDetail(
                    pm_id=task.pm_id,
                    pm_label=format_ltap_pm_label(task),
                    fm_id=task.fm_id,
                    taak_type=task.taak_type.value,
                    taak_omschrijving=task.taak_omschrijving,
                    executions=executions,
                    pm_cost_eur=task.cost_eur * executions,
                    planned_downtime_hr=_planned_downtime_per_execution(task) * executions,
                    anchor_year=anchor_year,
                    shiftable=_is_shiftable(task),
                )
            )

    years: list[LTAPYearRow] = []
    total_task_count = 0
    total_pm_cost_eur = 0.0
    total_planned_downtime_hr = 0.0
    for year in range(max_year + 1):
        details = tuple(sorted(by_year[year], key=lambda item: item.pm_id))
        task_count = sum(item.executions for item in details)
        pm_cost = sum(item.pm_cost_eur for item in details)
        downtime = sum(item.planned_downtime_hr for item in details)
        years.append(
            LTAPYearRow(
                year=year,
                task_count=task_count,
                pm_cost_eur=pm_cost,
                planned_downtime_hr=downtime,
                details=details,
            )
        )
        total_task_count += task_count
        total_pm_cost_eur += pm_cost
        total_planned_downtime_hr += downtime

    return LTAPView(
        years=tuple(years),
        total_task_count=total_task_count,
        total_pm_cost_eur=total_pm_cost_eur,
        total_planned_downtime_hr=total_planned_downtime_hr,
    )


def _executions_by_year(task: PMTask, *, lifecycle_years: float, anchor_year: float) -> dict[int, int]:
    interval = float(task.interval_jaar)
    if interval <= 0:
        return {}
    first_k = math.ceil((0.0 - anchor_year) / interval)
    last_k = math.floor(((lifecycle_years - 1e-9) - anchor_year) / interval)
    out: dict[int, int] = {}
    if last_k < first_k:
        return out
    for k in range(first_k, last_k + 1):
        t = anchor_year + k * interval
        year = int(math.floor(t))
        out[year] = out.get(year, 0) + 1
    return out


def _planned_downtime_per_execution(task: PMTask) -> float:
    if not task.causes_unavailability:
        return 0.0
    return task.duration.to_hours() * task.unavailability_fraction


def _is_shiftable(task: PMTask) -> bool:
    if task.taak_type == TaskType.SVO:
        return False
    return "WET" not in (task.taak_omschrijving or "").upper()


def format_ltap_pm_label(task: PMTask) -> str:
    group_label = "TG" if task.task_group_id else "GEEN-TG"
    wet_label = "WET" if "WET" in (task.taak_omschrijving or "").upper() else "NIET-WET"
    return f"{task.pm_id} [{task.taak_type.value}] [{group_label}] [{wet_label}]"
