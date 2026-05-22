"""Meekoppel apply bridge — preview + overlay-shift (slice 39, ADR-0005)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rcm_core.models import PMTask, RCMProject, TaskType

from rcm_desktop.adapter.meekoppelkansen_discovery_service import MeekoppelSuggestion
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_whatif_service import WhatIfActionResult, apply_overlay_shift

MeekoppelAnchor = Literal["earlier", "later"]


@dataclass(frozen=True)
class MeekoppelPreview:
    shifted_pm_id: str
    shift_years: int
    from_year: int
    to_year: int
    blocked_reason: str | None = None
    pm_a: str = ""
    pm_b: str = ""


def effective_due_year(
    project: RCMProject,
    overlay: PlanningOverlayState,
    pm_id: str,
) -> int:
    task = project.pm_tasks.get(pm_id)
    if task is None:
        return 0
    base = int(round(task.interval_jaar))
    anchor = overlay.anchor_years_dict().get(pm_id, 0.0)
    return base + int(round(anchor))


def _blocked_reason_for_pm(task: PMTask | None) -> str | None:
    if task is None:
        return "Onbekende PM-taak."
    if task.taak_type == TaskType.SVO:
        return f"Taak '{task.pm_id}' (SVO) is niet verschuifbaar."
    if "WET" in (task.taak_omschrijving or "").upper():
        return f"Taak '{task.pm_id}' (wettelijk) is niet verschuifbaar."
    return None


def preview_meekoppel_suggestion(
    project: RCMProject,
    overlay: PlanningOverlayState,
    suggestion: MeekoppelSuggestion,
    *,
    anchor: MeekoppelAnchor = "earlier",
) -> MeekoppelPreview:
    eff_a = effective_due_year(project, overlay, suggestion.pm_a)
    eff_b = effective_due_year(project, overlay, suggestion.pm_b)
    block_a = _blocked_reason_for_pm(project.pm_tasks.get(suggestion.pm_a))
    block_b = _blocked_reason_for_pm(project.pm_tasks.get(suggestion.pm_b))
    blocked = block_a or block_b

    if anchor == "earlier":
        target = min(eff_a, eff_b)
        if eff_a > eff_b:
            shifted_pm = suggestion.pm_a
        elif eff_b > eff_a:
            shifted_pm = suggestion.pm_b
        else:
            shifted_pm = suggestion.pm_b
    else:
        target = max(eff_a, eff_b)
        if eff_a < eff_b:
            shifted_pm = suggestion.pm_a
        elif eff_b < eff_a:
            shifted_pm = suggestion.pm_b
        else:
            shifted_pm = suggestion.pm_a

    from_eff = effective_due_year(project, overlay, shifted_pm)
    shift_years = int(target - from_eff)

    return MeekoppelPreview(
        shifted_pm_id=shifted_pm,
        shift_years=shift_years,
        from_year=from_eff,
        to_year=target,
        blocked_reason=blocked,
        pm_a=suggestion.pm_a,
        pm_b=suggestion.pm_b,
    )


def apply_meekoppel_suggestion(
    project: RCMProject,
    overlay: PlanningOverlayState,
    suggestion: MeekoppelSuggestion,
    *,
    anchor: MeekoppelAnchor = "earlier",
) -> WhatIfActionResult:
    preview = preview_meekoppel_suggestion(project, overlay, suggestion, anchor=anchor)
    if preview.blocked_reason:
        return WhatIfActionResult(overlay=overlay, error=preview.blocked_reason)
    if preview.shift_years == 0:
        return WhatIfActionResult(overlay=overlay, error=None)
    return apply_overlay_shift(
        project,
        overlay,
        pm_ids=[preview.shifted_pm_id],
        shift_years=preview.shift_years,
    )
