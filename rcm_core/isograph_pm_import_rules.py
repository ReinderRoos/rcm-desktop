"""Import rules for PM vs FM effect links (PM-semantiek-spike, slice 35)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# AW RcmScheduledTasks.Type values that map to PM-effect scope (PEnable).
_PM_TASK_TYPES = frozenset({"Planned", "PM", "REV", "WET", "SVO", "TST"})
# Inspection scope (IEnable).
_IN_TASK_TYPES = frozenset({"Inspection", "IN", "Inspectie"})


def _truthy(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


@dataclass(frozen=True)
class CauseEffectAssignmentRow:
    """Subset of RcmCauseEffectAssignments row (AW export)."""

    cause_id: str
    effect_id: str
    c_enable: object
    p_enable: object
    i_enable: object
    redundancy_factor: object
    sub_index: object = 0


@dataclass(frozen=True)
class ScheduledTaskRow:
    """Subset of RcmScheduledTasks row used to resolve PM links."""

    cause_id: str
    sub_index: object
    task_id: str
    task_type: str
    enabled: object = True


def parse_redundancy_factor(raw: object) -> float:
    if raw is None or raw == "":
        return 1.0
    return float(raw)


def should_create_fm_effect_link(row: CauseEffectAssignmentRow) -> bool:
    """FM-effect: actief bij correctief falen (CEnable)."""
    return _truthy(row.c_enable)


def fm_effect_fractie(row: CauseEffectAssignmentRow) -> float:
    """RF = P(gevolg | falen) in AW → RCM2 FMEffectLink.fractie."""
    return parse_redundancy_factor(row.redundancy_factor)


def _task_matches_pm_scope(task_type: str, *, inspection: bool) -> bool:
    t = (task_type or "").strip()
    if inspection:
        return t in _IN_TASK_TYPES
    return t in _PM_TASK_TYPES


def resolve_pm_task_id(
    row: CauseEffectAssignmentRow,
    scheduled_tasks: list[ScheduledTaskRow],
) -> str | None:
    """Match assignment SubIndex + flags to exactly one scheduled task for Cause."""
    if not (_truthy(row.p_enable) or _truthy(row.i_enable)):
        return None
    sub = str(row.sub_index).strip() if row.sub_index is not None else "0"
    candidates: list[str] = []
    for task in scheduled_tasks:
        if task.cause_id != row.cause_id:
            continue
        if str(task.sub_index).strip() != sub:
            continue
        match = False
        if _truthy(row.p_enable) and _task_matches_pm_scope(task.task_type, inspection=False):
            match = True
        if _truthy(row.i_enable) and _task_matches_pm_scope(task.task_type, inspection=True):
            match = True
        if match:
            candidates.append(task.task_id)
    unique = sorted(set(candidates))
    if len(unique) == 1:
        return unique[0]
    return None


def should_create_pm_effect_link(
    row: CauseEffectAssignmentRow,
    scheduled_tasks: list[ScheduledTaskRow],
) -> bool:
    return resolve_pm_task_id(row, scheduled_tasks) is not None


def pm_effect_fractie_default() -> float:
    """AW RF is falen-conditional; PM fractie = deel taakduur met effect (default volledig)."""
    return 1.0


def pm_import_warning_unresolved(row: CauseEffectAssignmentRow) -> str | None:
    if not (_truthy(row.p_enable) or _truthy(row.i_enable)):
        return None
    if should_create_pm_effect_link(row, scheduled_tasks=[]):
        return None
    flags = []
    if _truthy(row.p_enable):
        flags.append("PEnable")
    if _truthy(row.i_enable):
        flags.append("IEnable")
    return (
        f"PM-effect niet geïmporteerd voor {row.cause_id} → {row.effect_id}: "
        f"{'+'.join(flags)} zonder resolvable ScheduledTask (Cause, SubIndex)."
    )
