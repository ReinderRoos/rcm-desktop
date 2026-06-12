"""QSettings-seam voor FM-resultaten kolomzichtbaarheid (slice 80)."""

from __future__ import annotations

from typing import Protocol

from rcm_desktop.adapter.fm_results_column_policy import (
    DEFAULT_HIDDEN_FM_OPTIONAL_COLUMNS,
    FM_OPTIONAL_COLUMN_IDS,
)

FM_RESULTS_HIDDEN_COLUMNS_KEY = "workspace/fm_results/hidden_optional_columns"


class _SettingsLike(Protocol):
    def value(self, key: str, default: object = None, type: type | None = None) -> object: ...
    def setValue(self, key: str, value: object) -> None: ...


def _normalize_hidden(raw: object, *, key_present: bool) -> frozenset[str]:
    if not key_present:
        return frozenset(DEFAULT_HIDDEN_FM_OPTIONAL_COLUMNS)
    if not isinstance(raw, str):
        return frozenset(DEFAULT_HIDDEN_FM_OPTIONAL_COLUMNS)
    if not raw.strip():
        return frozenset()
    ids = frozenset(part.strip() for part in raw.split(",") if part.strip())
    return frozenset(col_id for col_id in ids if col_id in FM_OPTIONAL_COLUMN_IDS)


def read_fm_hidden_optional_columns(settings: _SettingsLike) -> frozenset[str]:
    key_present = settings.value(FM_RESULTS_HIDDEN_COLUMNS_KEY) is not None
    stored = settings.value(FM_RESULTS_HIDDEN_COLUMNS_KEY, "")
    return _normalize_hidden(stored, key_present=key_present)


def write_fm_hidden_optional_columns(
    settings: _SettingsLike,
    hidden_ids: frozenset[str],
) -> None:
    valid = frozenset(col_id for col_id in hidden_ids if col_id in FM_OPTIONAL_COLUMN_IDS)
    settings.setValue(FM_RESULTS_HIDDEN_COLUMNS_KEY, ",".join(sorted(valid)))
