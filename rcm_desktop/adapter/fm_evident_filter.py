"""Filter FM-resultaatrijen op merkbaar vs niet-merkbaar falen."""

from __future__ import annotations

from typing import Literal

from rcm_core.models import RCMProject
from rcm_desktop.adapter.result_view_service import FMResultRow

EvidentFilter = Literal["all", "nmf_only", "evident_only"]


def filter_fm_rows_by_evident(
    rows: list[FMResultRow] | tuple[FMResultRow, ...],
    project: RCMProject,
    evident_filter: EvidentFilter,
) -> list[FMResultRow]:
    if evident_filter == "all":
        return list(rows)
    filtered: list[FMResultRow] = []
    for row in rows:
        fm = project.faalwijzes.get(row.fm_id)
        if fm is None:
            continue
        if evident_filter == "nmf_only" and not fm.is_evident:
            filtered.append(row)
        elif evident_filter == "evident_only" and fm.is_evident:
            filtered.append(row)
    return filtered
