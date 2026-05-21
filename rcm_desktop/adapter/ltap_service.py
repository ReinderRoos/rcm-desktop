from __future__ import annotations

from dataclasses import dataclass
import math

from rcm_core.models import PMTask, RCMProject, TaskType

PM_COST_DISPLAY_NORMAL = "normal"
PM_COST_DISPLAY_ZERO_EXPECTED = "zero_expected"
PM_COST_DISPLAY_ZERO_MISSING = "zero_missing"


@dataclass(frozen=True)
class LTAPTaskDetail:
    pm_id: str
    pm_label: str
    fm_id: str
    fm_display: str
    fm_tooltip: str
    taak_type: str
    taak_omschrijving: str
    executions: int
    pm_cost_eur: float
    pm_cost_display: str
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


def resolve_ltap_fm_cell(*, fm_id: str, project: RCMProject) -> tuple[str, str]:
    """Return (cell_display_text, cell_tooltip) for the LTAP Faalwijze column."""
    fm = project.faalwijzes.get(fm_id)
    if fm is None:
        tip = (
            f"Faalwijze-ID (JSON): {fm_id}\n"
            "Onbekende faalwijze: deze FM staat niet in het geladen project."
        )
        return (fm_id, tip)
    desc = (fm.faalwijze_omschrijving or "").strip()
    base_tip = f"Faalwijze-ID (JSON): {fm_id}"
    if not desc:
        return (fm_id, f"{base_tip}\nGeen omschrijving in het model.")
    return (desc, base_tip)


def _task_matches_type_filter(task: PMTask, taak_type_filter: str | None) -> bool:
    if taak_type_filter is None:
        return True
    if taak_type_filter == "WET":
        return task.is_wettelijk_verplicht or "WET" in (task.taak_omschrijving or "").upper()
    return task.taak_type.value == taak_type_filter


def build_ltap_view(
    project: RCMProject,
    *,
    overlay_anchor_years: dict[str, float] | None = None,
    taak_type_filter: str | None = None,
    disabled_pm_ids: frozenset[str] | None = None,
    fm_pbs_ids: frozenset[str] | None = None,
) -> LTAPView:
    lifecycle_years = float(project.config.lifecycle_years)
    max_year = max(0, math.ceil(lifecycle_years) - 1)
    by_year: dict[int, list[LTAPTaskDetail]] = {year: [] for year in range(max_year + 1)}
    seq_by_pm_id = build_ltap_pm_display_seq_map(project)

    disabled = disabled_pm_ids or frozenset()
    for task in sorted(project.pm_tasks.values(), key=lambda item: item.pm_id):
        if task.pm_id in disabled:
            continue
        if fm_pbs_ids is not None:
            fm = project.faalwijzes.get(task.fm_id)
            if fm is None or fm.pbs_id not in fm_pbs_ids:
                continue
        if not _task_matches_type_filter(task, taak_type_filter):
            continue
        anchor_year = float((overlay_anchor_years or {}).get(task.pm_id, 0.0))
        executions_by_year = _executions_by_year(task, lifecycle_years=lifecycle_years, anchor_year=anchor_year)
        for year, executions in executions_by_year.items():
            if executions <= 0:
                continue
            fm_display, fm_tooltip = resolve_ltap_fm_cell(fm_id=task.fm_id, project=project)
            by_year[year].append(
                LTAPTaskDetail(
                    pm_id=task.pm_id,
                    pm_label=format_ltap_pm_label(task, seq_by_pm_id[task.pm_id]),
                    fm_id=task.fm_id,
                    fm_display=fm_display,
                    fm_tooltip=fm_tooltip,
                    taak_type=task.taak_type.value,
                    taak_omschrijving=task.taak_omschrijving,
                    executions=executions,
                    pm_cost_eur=task.cost_eur * executions,
                    pm_cost_display=classify_pm_cost_display(task, project),
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


def build_ltap_pm_display_seq_map(project: RCMProject) -> dict[str, int]:
    ids = sorted(project.pm_tasks.keys())
    return {pm_id: idx + 1 for idx, pm_id in enumerate(ids)}


def classify_pm_cost_display(task: PMTask, project: RCMProject) -> str:
    if float(task.cost_eur) != 0.0:
        return PM_COST_DISPLAY_NORMAL
    if task.task_group_id:
        return PM_COST_DISPLAY_ZERO_EXPECTED
    rationale = task.effective_aanname_kosten(project)
    if rationale and rationale.strip():
        return PM_COST_DISPLAY_ZERO_EXPECTED
    return PM_COST_DISPLAY_ZERO_MISSING


def format_ltap_pm_label(task: PMTask, seq: int) -> str:
    parts = ["PM", task.taak_type.value]
    if "WET" in (task.taak_omschrijving or "").upper():
        parts.append("WET")
    if task.task_group_id:
        parts.append("TG")
    parts.append(f"{seq:02d}")
    return "_".join(parts)
