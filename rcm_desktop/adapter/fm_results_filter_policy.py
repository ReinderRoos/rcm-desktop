"""FM-resultaten kolomfilter-configuratie (slice 81)."""

from __future__ import annotations

from rcm_desktop.adapter.fm_results_sort_policy import (
    FM_COL_DOWNTIME,
    FM_COL_FAALMOMENTEN,
    FM_COL_KOSTEN,
)
from rcm_desktop.adapter.table_filter_parser import TableColumnFilterKind

FM_COL_FM_ID = 0
FM_COL_BOUWDEEL = 1
FM_COL_FAALWIJZE = 2
FM_COL_NMF = 3
FM_COL_RF = 4
FM_COL_PBS_ID = 8

FM_FILTER_TEXT_COLUMNS = frozenset({FM_COL_FM_ID, FM_COL_BOUWDEEL, FM_COL_FAALWIJZE, FM_COL_PBS_ID})
FM_FILTER_BOOL_COLUMNS = frozenset({FM_COL_NMF})
FM_FILTER_NUMERIC_COLUMNS = frozenset(
    {FM_COL_RF, FM_COL_FAALMOMENTEN, FM_COL_DOWNTIME, FM_COL_KOSTEN}
)

FM_FILTER_COLUMN_KINDS: dict[int, TableColumnFilterKind] = {
    FM_COL_FM_ID: TableColumnFilterKind.TEXT,
    FM_COL_BOUWDEEL: TableColumnFilterKind.TEXT,
    FM_COL_FAALWIJZE: TableColumnFilterKind.TEXT,
    FM_COL_NMF: TableColumnFilterKind.BOOL,
    FM_COL_RF: TableColumnFilterKind.NUMERIC,
    FM_COL_FAALMOMENTEN: TableColumnFilterKind.NUMERIC,
    FM_COL_DOWNTIME: TableColumnFilterKind.NUMERIC,
    FM_COL_KOSTEN: TableColumnFilterKind.NUMERIC,
    FM_COL_PBS_ID: TableColumnFilterKind.TEXT,
}
