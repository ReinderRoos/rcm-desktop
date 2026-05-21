"""Selectie-helpers voor LCC-jaardetail (slice 30)."""

from __future__ import annotations

from rcm_core.models import TaskType

from rcm_desktop.adapter.lcc_planning_service import LCCYearDetailView


def rev_row_indices(view: LCCYearDetailView) -> tuple[int, ...]:
    """Rij-indexen van zichtbare REV-taken in jaardetail (geen passieve rijen)."""
    return tuple(
        i
        for i, row in enumerate(view.rows)
        if row.taak_type == TaskType.REV.value and not row.is_passive
    )
