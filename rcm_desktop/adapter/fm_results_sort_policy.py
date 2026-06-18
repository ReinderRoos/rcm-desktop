"""Qt-vrije default-sortering voor FM-resultaten (slice 80; slice 104 compact layout)."""

from __future__ import annotations

from rcm_desktop.adapter.fm_results_filter_policy import FM_COL_METRIC

# Legacy column indices (wide table); compact single-run uses FM_COL_METRIC only.
FM_COL_FAALMOMENTEN = FM_COL_METRIC
FM_COL_DOWNTIME = FM_COL_METRIC
FM_COL_KOSTEN = FM_COL_METRIC


def default_fm_sort_column(metric: str) -> int:
    del metric
    return FM_COL_METRIC
