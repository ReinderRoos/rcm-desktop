"""Import rules for PM vs FM effect links (PM-semantiek-spike, slice 35; slice 69 alignment)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

# AW RcmScheduledTasks.Type values that map to PM-effect scope (PEnable).
_PM_TASK_TYPES = frozenset({"Planned", "PM", "REV", "WET", "SVO", "TST"})
# Inspection scope (IEnable).
_IN_TASK_TYPES = frozenset({"Inspection", "IN", "Inspectie"})

PmScope = Literal["planned", "inspection"]

_RF_SUFFIX_RE = re.compile(r"\[RF\s*=\s*([^\]]+)\]", re.IGNORECASE)


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


@dataclass(frozen=True)
class ResolvedPmTask:
    """PM-taak opgelost uit ScheduledTasks (pm_id gebruikt task-SubIndex)."""

    pm_id: str
    task_id: str
    sub_index: str


@dataclass(frozen=True)
class ParsedEffectId:
    effect_id: str
    redundancy_factor: float | None


def parse_redundancy_factor(raw: object) -> float:
    if raw is None or raw == "":
        return 1.0
    if isinstance(raw, str):
        text = raw.strip().replace(",", ".")
        if not text:
            return 1.0
        return float(text)
    return float(raw)


def _split_effect_ids_segments(text: str) -> list[str]:
    """Split op komma's buiten `[RF=…]`-suffixen (NL decimaal met komma)."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for char in text:
        if char == "[":
            depth += 1
        elif char == "]":
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            segment = "".join(current).strip()
            if segment:
                parts.append(segment)
            current = []
            continue
        current.append(char)
    segment = "".join(current).strip()
    if segment:
        parts.append(segment)
    return parts


def parse_effect_ids(text: object) -> list[ParsedEffectId]:
    """Parse RcmCauses.EffectIds vrije tekst (komma-gescheiden, optioneel [RF=0,1])."""
    if text is None or str(text).strip() == "":
        return []
    parts = _split_effect_ids_segments(str(text))
    out: list[ParsedEffectId] = []
    for part in parts:
        match = _RF_SUFFIX_RE.search(part)
        if match:
            rf = parse_redundancy_factor(match.group(1))
            effect_id = part[: match.start()].strip()
        else:
            rf = None
            effect_id = part.strip()
        if effect_id:
            out.append(ParsedEffectId(effect_id=effect_id, redundancy_factor=rf))
    return out


def audit_effect_ids_vs_fm_links(
    effect_ids_text: object,
    fm_links: list[tuple[str, float]],
) -> str | None:
    """Cross-check EffectIds-tekst tegen geïmporteerde FM-links (cause-niveau)."""
    parsed = parse_effect_ids(effect_ids_text)
    if not parsed:
        return None
    fm_by_effect: dict[str, list[float]] = {}
    for effect_id, fractie in fm_links:
        fm_by_effect.setdefault(effect_id, []).append(fractie)
    missing: list[str] = []
    rf_mismatch: list[str] = []
    for item in parsed:
        fractions = fm_by_effect.get(item.effect_id)
        if not fractions:
            missing.append(item.effect_id)
            continue
        if item.redundancy_factor is not None:
            target = item.redundancy_factor
            if not any(abs(f - target) < 1e-6 for f in fractions):
                rf_mismatch.append(f"{item.effect_id} [RF={target}]")
    if not missing and not rf_mismatch:
        return None
    parts: list[str] = []
    if missing:
        parts.append(f"ontbrekend in assignments: {', '.join(missing)}")
    if rf_mismatch:
        parts.append(f"RF-wijkt af: {', '.join(rf_mismatch)}")
    return "EffectIds-mismatch: " + "; ".join(parts)


def should_create_fm_effect_link(row: CauseEffectAssignmentRow) -> bool:
    """FM-effect: actief bij correctief falen (CEnable)."""
    return _truthy(row.c_enable)


def fm_effect_fractie(row: CauseEffectAssignmentRow) -> float:
    """RF = P(gevolg | falen) in AW → RCM2 FMEffectLink.fractie."""
    return parse_redundancy_factor(row.redundancy_factor)


def pm_effect_fractie(row: CauseEffectAssignmentRow) -> float:
    """Slice 69: zelfde RF als CM op dezelfde assignment-rij."""
    return parse_redundancy_factor(row.redundancy_factor)


def pm_effect_fractie_default() -> float:
    """Backward-compat alias; prefer :func:`pm_effect_fractie`."""
    return 1.0


def _task_matches_pm_scope(task_type: str, *, inspection: bool) -> bool:
    t = (task_type or "").strip()
    if inspection:
        return t in _IN_TASK_TYPES
    return t in _PM_TASK_TYPES


def _assignment_sub_index(row: CauseEffectAssignmentRow) -> str:
    return str(row.sub_index).strip() if row.sub_index is not None else "0"


def _task_sub_index(task: ScheduledTaskRow) -> str:
    return str(task.sub_index).strip() if task.sub_index is not None else "0"


def _to_resolved(task: ScheduledTaskRow) -> ResolvedPmTask:
    sub = _task_sub_index(task)
    pm_id = f"{task.cause_id}|{task.task_id}|{sub}"
    return ResolvedPmTask(pm_id=pm_id, task_id=task.task_id, sub_index=sub)


def _tasks_in_scope(
    scheduled_tasks: list[ScheduledTaskRow],
    cause_id: str,
    scope: PmScope,
) -> list[ScheduledTaskRow]:
    inspection = scope == "inspection"
    return [
        t
        for t in scheduled_tasks
        if t.cause_id == cause_id
        and _task_matches_pm_scope(t.task_type, inspection=inspection)
    ]


def _scope_enabled(row: CauseEffectAssignmentRow, scope: PmScope) -> bool:
    if scope == "planned":
        return _truthy(row.p_enable)
    return _truthy(row.i_enable)


def _unique_resolved_from_tasks(tasks: list[ScheduledTaskRow]) -> list[ResolvedPmTask]:
    by_pm_id = {_to_resolved(t).pm_id: _to_resolved(t) for t in tasks}
    return sorted(by_pm_id.values(), key=lambda r: r.pm_id)


def resolve_pm_tasks_for_scope(
    row: CauseEffectAssignmentRow,
    scheduled_tasks: list[ScheduledTaskRow],
    scope: PmScope,
    *,
    allow_subindex_fallback: bool = True,
) -> tuple[list[ResolvedPmTask], list[str]]:
    """Resolve PM-taken voor één scope (Planned of Inspection)."""
    if not _scope_enabled(row, scope):
        return [], []
    warnings: list[str] = []
    sub = _assignment_sub_index(row)
    scope_tasks = _tasks_in_scope(scheduled_tasks, row.cause_id, scope)
    exact = [t for t in scope_tasks if _task_sub_index(t) == sub]
    if len(exact) == 1:
        return [_to_resolved(exact[0])], warnings
    if len(exact) > 1:
        task_ids = sorted({t.task_id for t in exact})
        if len(task_ids) == 1:
            return [_to_resolved(exact[0])], warnings
        return [], []
    if not allow_subindex_fallback or not scope_tasks:
        return [], []
    if len(scope_tasks) == 1:
        task = scope_tasks[0]
        warnings.append(
            f"SubIndex-fallback: {row.cause_id} → {row.effect_id} "
            f"({scope}) assignment SubIndex={sub} → task SubIndex={_task_sub_index(task)}"
        )
        return [_to_resolved(task)], warnings
    return [], []


def resolve_pm_tasks(
    row: CauseEffectAssignmentRow,
    scheduled_tasks: list[ScheduledTaskRow],
) -> tuple[list[ResolvedPmTask], list[str]]:
    """Resolve alle PM-taken voor PEnable en IEnable (dual-scope)."""
    resolved: list[ResolvedPmTask] = []
    warnings: list[str] = []
    for scope in ("planned", "inspection"):
        scope_resolved, scope_warnings = resolve_pm_tasks_for_scope(
            row, scheduled_tasks, scope
        )
        resolved.extend(scope_resolved)
        warnings.extend(scope_warnings)
    by_pm_id = {r.pm_id: r for r in resolved}
    return sorted(by_pm_id.values(), key=lambda r: r.pm_id), warnings


def resolve_pm_task_id(
    row: CauseEffectAssignmentRow,
    scheduled_tasks: list[ScheduledTaskRow],
) -> str | None:
    """Backward-compat: één task_id wanneer precies één PM-taak resolved."""
    resolved, _ = resolve_pm_tasks(row, scheduled_tasks)
    if len(resolved) == 1:
        return resolved[0].task_id
    return None


def should_create_pm_effect_link(
    row: CauseEffectAssignmentRow,
    scheduled_tasks: list[ScheduledTaskRow],
) -> bool:
    resolved, _ = resolve_pm_tasks(row, scheduled_tasks)
    return len(resolved) > 0


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


def pm_import_warning_unresolved_with_tasks(
    row: CauseEffectAssignmentRow,
    scheduled_tasks: list[ScheduledTaskRow],
) -> str | None:
    if not (_truthy(row.p_enable) or _truthy(row.i_enable)):
        return None
    resolved, _ = resolve_pm_tasks(row, scheduled_tasks)
    if resolved:
        return None
    return pm_import_warning_unresolved(row)


def summarize_import_warnings(warnings: list[str]) -> dict[str, int]:
    """Tel importwaarschuwingen per categorie (slice 69 rapportage)."""
    counts = {
        "unresolved_pm": 0,
        "subindex_fallback": 0,
        "effect_ids_mismatch": 0,
        "other": 0,
    }
    for w in warnings:
        low = w.lower()
        if "pm-effect niet geïmporteerd" in low:
            counts["unresolved_pm"] += 1
        elif "subindex-fallback" in low:
            counts["subindex_fallback"] += 1
        elif "effectids-mismatch" in low:
            counts["effect_ids_mismatch"] += 1
        else:
            counts["other"] += 1
    return counts
