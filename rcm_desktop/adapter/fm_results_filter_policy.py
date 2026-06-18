"""FM-resultaten kolomfilter-configuratie (slice 81; slice 104 compact layout)."""

from __future__ import annotations

from rcm_desktop.adapter.table_filter_parser import TableColumnFilterKind

FM_COL_FM_ID = 0
FM_COL_BOUWDEEL = 1
FM_COL_FAALWIJZE = 2
FM_COL_METRIC = 3
FM_COL_NMF = 4
FM_COL_RF = 5

# Legacy aliases for tests that reference metric-specific columns (compact: one metric col).
FM_COL_FAALMOMENTEN = FM_COL_METRIC
FM_COL_DOWNTIME = FM_COL_METRIC
FM_COL_KOSTEN = FM_COL_METRIC
FM_COL_PBS_ID = -1

FM_FILTER_TEXT_COLUMNS = frozenset({FM_COL_FM_ID, FM_COL_BOUWDEEL, FM_COL_FAALWIJZE})
FM_FILTER_BOOL_COLUMNS = frozenset({FM_COL_NMF})
FM_FILTER_NUMERIC_COLUMNS = frozenset({FM_COL_METRIC, FM_COL_RF})

FM_FILTER_COLUMN_KINDS: dict[int, TableColumnFilterKind] = {
    FM_COL_FM_ID: TableColumnFilterKind.TEXT,
    FM_COL_BOUWDEEL: TableColumnFilterKind.TEXT,
    FM_COL_FAALWIJZE: TableColumnFilterKind.TEXT,
    FM_COL_METRIC: TableColumnFilterKind.NUMERIC,
    FM_COL_NMF: TableColumnFilterKind.BOOL,
    FM_COL_RF: TableColumnFilterKind.NUMERIC,
}
