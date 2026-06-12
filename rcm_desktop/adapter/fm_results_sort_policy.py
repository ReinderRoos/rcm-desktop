"""Qt-vrije default-sortering voor FM-resultaten (slice 80)."""

from __future__ import annotations

from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
)

FM_COL_FAALMOMENTEN = 5
FM_COL_DOWNTIME = 6
FM_COL_KOSTEN = 7


def default_fm_sort_column(metric: str) -> int:
    if metric == METRIC_FAALMOMENTEN:
        return FM_COL_FAALMOMENTEN
    if metric == METRIC_KOSTEN:
        return FM_COL_KOSTEN
    return FM_COL_DOWNTIME
