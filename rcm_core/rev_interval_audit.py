"""REV-interval parity-audit (D1/D2 diagnostiek, slice 67)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.fm_parity_diagnostics import compute_rev_diagnostics
from rcm_core.models import RCMProject, TaskType


@dataclass(frozen=True)
class RevIntervalMismatch:
    fm_id: str
    active_moments: int
    structural_moments: int
    active_intervals_years: tuple[float, ...]


@dataclass(frozen=True)
class RevIntervalAudit:
    """FM's waar actief REV-schema afwijkt van structureel (overlay-effect)."""

    overlay_only_fms: tuple[RevIntervalMismatch, ...]
    fm_count: int


def audit_rev_interval_parity(project: RCMProject) -> RevIntervalAudit:
    overlay_only: list[RevIntervalMismatch] = []
    for fm_id in sorted(project.faalwijzes):
        fm = project.faalwijzes[fm_id]
        if fm.failure_type.value != "aging":
            continue
        rev_tasks = [
            t
            for t in project.get_pm_tasks_for_fm(fm_id)
            if t.taak_type == TaskType.REV
        ]
        if not rev_tasks:
            continue
        diag = compute_rev_diagnostics(project, fm_id)
        if diag.active_moments != diag.structural_moments:
            overlay_only.append(
                RevIntervalMismatch(
                    fm_id=fm_id,
                    active_moments=diag.active_moments,
                    structural_moments=diag.structural_moments,
                    active_intervals_years=diag.active_intervals_years,
                )
            )
    return RevIntervalAudit(
        overlay_only_fms=tuple(overlay_only),
        fm_count=len(project.faalwijzes),
    )
