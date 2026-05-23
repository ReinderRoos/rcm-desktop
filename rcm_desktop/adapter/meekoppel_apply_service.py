"""Meekoppel apply bridge — preview + overlay-shift (slice 40, ADR-0005)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rcm_core.models import PMTask, RCMProject, TaskType

from rcm_desktop.adapter.meekoppelkansen_discovery_service import MeekoppelLocationGroup
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_whatif_service import WhatIfActionResult

MeekoppelAnchor = Literal["earlier", "later"]


@dataclass(frozen=True)
class MeekoppelShiftMove:
    pm_id: str
    from_year: int
    to_year: int
    shift_years: int


@dataclass(frozen=True)
class MeekoppelLocationPreview:
    pbs_id: str
    path_label: str
    target_year: int
    moves: tuple[MeekoppelShiftMove, ...]
    blocked_reason: str | None = None


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


def preview_meekoppel_location(
    project: RCMProject,
    overlay: PlanningOverlayState,
    group: MeekoppelLocationGroup,
    *,
    anchor: MeekoppelAnchor = "later",
) -> MeekoppelLocationPreview:
    effective_years = [
        effective_due_year(project, overlay, t.pm_id) for t in group.tasks
    ]
    for t in group.tasks:
        blocked = _blocked_reason_for_pm(project.pm_tasks.get(t.pm_id))
        if blocked:
            return MeekoppelLocationPreview(
                pbs_id=group.pbs_id,
                path_label=group.path_label,
                target_year=0,
                moves=(),
                blocked_reason=blocked,
            )

    target = min(effective_years) if anchor == "earlier" else max(effective_years)
    moves: list[MeekoppelShiftMove] = []
    for t, eff in zip(group.tasks, effective_years, strict=True):
        shift = int(target - eff)
        if shift == 0:
            continue
        moves.append(
            MeekoppelShiftMove(
                pm_id=t.pm_id,
                from_year=eff,
                to_year=target,
                shift_years=shift,
            )
        )
    return MeekoppelLocationPreview(
        pbs_id=group.pbs_id,
        path_label=group.path_label,
        target_year=target,
        moves=tuple(moves),
        blocked_reason=None,
    )


def apply_meekoppel_location(
    project: RCMProject,
    overlay: PlanningOverlayState,
    group: MeekoppelLocationGroup,
    *,
    anchor: MeekoppelAnchor = "later",
) -> WhatIfActionResult:
    preview = preview_meekoppel_location(project, overlay, group, anchor=anchor)
    if preview.blocked_reason:
        return WhatIfActionResult(overlay=overlay, error=preview.blocked_reason)
    if not preview.moves:
        return WhatIfActionResult(overlay=overlay, error=None)

    anchors = dict(overlay.anchor_years_dict())
    for move in preview.moves:
        task = project.pm_tasks.get(move.pm_id)
        blocked = _blocked_reason_for_pm(task)
        if task is None or blocked is not None:
            blocked = blocked or "Onbekende PM-taak."
            return WhatIfActionResult(overlay=overlay, error=blocked)
        anchors[move.pm_id] = float(anchors.get(move.pm_id, 0.0) + move.shift_years)
    return WhatIfActionResult(
        overlay=overlay.with_anchor_years(anchors),
        error=None,
    )
