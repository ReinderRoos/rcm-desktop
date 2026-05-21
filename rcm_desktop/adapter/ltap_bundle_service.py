from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import PMTask, RCMProject, TaskType


@dataclass(frozen=True)
class BundleShiftResult:
    ok: bool
    overlay_anchor_years: dict[str, float]
    error: str | None = None


def apply_bundle_shift(
    project: RCMProject,
    *,
    current_overlay_anchor_years: dict[str, float],
    pm_ids: list[str],
    shift_years: int,
) -> BundleShiftResult:
    if not pm_ids:
        return BundleShiftResult(ok=False, overlay_anchor_years=dict(current_overlay_anchor_years), error="Geen PM-taak geselecteerd.")
    out = dict(current_overlay_anchor_years)
    seen: set[str] = set()
    for pm_id in pm_ids:
        if pm_id in seen:
            continue
        seen.add(pm_id)
        task = project.pm_tasks.get(pm_id)
        if task is None:
            return BundleShiftResult(
                ok=False,
                overlay_anchor_years=dict(current_overlay_anchor_years),
                error=f"Bundelactie geblokkeerd: onbekende PM-taak '{pm_id}'.",
            )
        if not _is_shiftable(task):
            return BundleShiftResult(
                ok=False,
                overlay_anchor_years=dict(current_overlay_anchor_years),
                error=f"Bundelactie geblokkeerd: taak '{pm_id}' ({task.taak_type.value}) is niet verschuifbaar.",
            )
        out[pm_id] = float(out.get(pm_id, 0.0) + shift_years)
    return BundleShiftResult(ok=True, overlay_anchor_years=out, error=None)


def reset_overlay() -> dict[str, float]:
    return {}


def _is_shiftable(task: PMTask) -> bool:
    if task.taak_type == TaskType.SVO:
        return False
    return "WET" not in (task.taak_omschrijving or "").upper()
