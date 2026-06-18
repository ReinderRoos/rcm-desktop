"""QSettings-seam voor Kolom-fit-modus (slice 75)."""

from __future__ import annotations

from typing import Protocol

from rcm_desktop.adapter.column_fit_policy import ColumnFitMode, default_column_fit_mode

FM_DETAIL_COLUMN_FIT_SETTINGS_KEY = "workspace/fm_detail/column_fit_mode"


class _SettingsLike(Protocol):
    def value(self, key: str, default: object = ..., type: type | None = None) -> object: ...

    def setValue(self, key: str, value: object) -> None: ...


def column_fit_mode_from_settings_value(raw: object | None) -> ColumnFitMode:
    if raw == ColumnFitMode.BIJGESNEDEN.value:
        return ColumnFitMode.BIJGESNEDEN
    return default_column_fit_mode()


def column_fit_mode_from_crop_checked(checked: bool) -> ColumnFitMode:
    if checked:
        return ColumnFitMode.BIJGESNEDEN
    return ColumnFitMode.PASSEND


def crop_checked_from_column_fit_mode(mode: ColumnFitMode) -> bool:
    return mode is ColumnFitMode.BIJGESNEDEN


def read_fm_detail_column_fit_mode(settings: _SettingsLike) -> ColumnFitMode:
    raw = settings.value(FM_DETAIL_COLUMN_FIT_SETTINGS_KEY, default_column_fit_mode().value)
    return column_fit_mode_from_settings_value(raw)


def write_fm_detail_column_fit_mode(settings: _SettingsLike, mode: ColumnFitMode) -> None:
    settings.setValue(FM_DETAIL_COLUMN_FIT_SETTINGS_KEY, mode.value)
