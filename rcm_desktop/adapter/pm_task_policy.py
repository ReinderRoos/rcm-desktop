"""PM task policy — shiftability and wettelijk labeling (adapter SSOT)."""

from __future__ import annotations

from rcm_core.models import PMTask, TaskType


def is_pm_wettelijk(task: PMTask) -> bool:
    """True when taak wettelijk verplicht is (vlag of WET-markering in omschrijving)."""
    return bool(task.is_wettelijk_verplicht) or "WET" in (task.taak_omschrijving or "").upper()


def is_pm_wettelijk_from_import_fields(
    *,
    aw_type: str,
    task_id: str,
    description: str,
) -> bool:
    """Wettelijk-detectie tijdens Isograph-import (Type, TaskId, Description)."""
    return (
        "WET" in aw_type.upper()
        or "WET" in task_id.upper()
        or "WET" in description.upper()
    )


def is_pm_shiftable(task: PMTask) -> bool:
    """True wanneer taak via planning-overlay verschoven mag worden."""
    if task.taak_type == TaskType.SVO:
        return False
    return not is_pm_wettelijk(task)


def pm_shift_block_reason(task: PMTask | None) -> str | None:
    """Gebruikersfacing reden wanneer shift geblokkeerd is; None = toegestaan."""
    if task is None:
        return "Onbekende PM-taak."
    if task.taak_type == TaskType.SVO:
        return f"Taak '{task.pm_id}' (SVO) is niet verschuifbaar."
    if is_pm_wettelijk(task):
        return f"Taak '{task.pm_id}' (wettelijk) is niet verschuifbaar."
    return None
