"""What-if shift/passief op planning overlay (slice 28)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import RCMProject

from rcm_desktop.adapter.ltap_bundle_service import apply_bundle_shift
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState


@dataclass(frozen=True)
class WhatIfActionResult:
    overlay: PlanningOverlayState
    error: str | None = None


def apply_overlay_shift(
    project: RCMProject,
    overlay: PlanningOverlayState,
    *,
    pm_ids: list[str],
    shift_years: int,
) -> WhatIfActionResult:
    if not overlay.active:
        return WhatIfActionResult(overlay=overlay, error="What-if planning is niet actief.")
    result = apply_bundle_shift(
        project,
        current_overlay_anchor_years=overlay.anchor_years_dict(),
        pm_ids=pm_ids,
        shift_years=shift_years,
    )
    if not result.ok:
        return WhatIfActionResult(overlay=overlay, error=result.error)
    return WhatIfActionResult(
        overlay=overlay.with_anchor_years(result.overlay_anchor_years),
        error=None,
    )
