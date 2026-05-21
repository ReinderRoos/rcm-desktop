"""Centrale UI-constanten voor tabellen (slice 18)."""

from __future__ import annotations

# Maximale sectiebreedte voor langlopende tekstkolommen (ResizeToContents + cap).
TEXT_COL_MAX_WIDTH_COMPACT = 440
TEXT_COL_MAX_WIDTH_WIDE = 680

SETTINGS_TABLE_WORD_WRAP_KEY = "tables/word_wrap"

# Max rijen waarvoor resizeRowsToContents nog mag lopen bij tekstomloop (slice 19).
ROW_RESIZE_MAX_ROWS_FAALWIJZEN = 400
ROW_RESIZE_MAX_ROWS_FM_RESULTS = 600
ROW_RESIZE_MAX_ROWS_LTAP_DETAIL = 600

# PBS-boom: max knopen om uit te klappen bij actieve substring-filter (slice 25).
# Voorkomt `expandAll()` op enorme zichtbare subsets.
PBS_FILTER_MAX_EXPAND_NODES = 500
