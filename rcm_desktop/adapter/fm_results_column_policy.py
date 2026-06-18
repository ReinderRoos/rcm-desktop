"""Qt-vrije optionele kolommen voor FM-resultaten (slice 80)."""

from __future__ import annotations

FM_COL_PBS_ID = 8

FM_OPTIONAL_COLUMN_IDS: frozenset[str] = frozenset({"pbs_id"})

FM_OPTIONAL_COLUMN_BY_ID: dict[str, int] = {
    "pbs_id": FM_COL_PBS_ID,
}

DEFAULT_HIDDEN_FM_OPTIONAL_COLUMNS: frozenset[str] = frozenset({"pbs_id"})


def optional_column_indices(hidden_ids: frozenset[str]) -> dict[str, bool]:
    """Map optionele kolom-id → zichtbaar (True = tonen)."""
    return {
        col_id: col_id not in hidden_ids for col_id in FM_OPTIONAL_COLUMN_IDS
    }
