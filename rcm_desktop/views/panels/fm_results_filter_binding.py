"""FM-resultaten filterrij — Qt-binding (slice 81)."""

from __future__ import annotations

from PySide6.QtWidgets import QTableView

from rcm_desktop.adapter.fm_results_filter_policy import (
    FM_FILTER_BOOL_COLUMNS,
    FM_FILTER_COLUMN_KINDS,
    FM_FILTER_NUMERIC_COLUMNS,
    FM_FILTER_TEXT_COLUMNS,
)
from rcm_desktop.adapter.table_column_filter_proxy import TableColumnFilterProxy
from rcm_desktop.views.widgets.table_filter_row import TableFilterRowWidget


def build_fm_table_filter_row(parent=None) -> TableFilterRowWidget:
    return TableFilterRowWidget(FM_FILTER_COLUMN_KINDS, parent=parent)


def apply_fm_filter_row_to_proxy(
    filter_row: TableFilterRowWidget,
    proxy: TableColumnFilterProxy,
) -> None:
    for col in FM_FILTER_TEXT_COLUMNS:
        proxy.set_text_filter(col, filter_row.text_value(col))
    for col in FM_FILTER_BOOL_COLUMNS:
        proxy.set_bool_filter(col, filter_row.bool_value(col))
    for col in FM_FILTER_NUMERIC_COLUMNS:
        proxy.set_numeric_filter(col, filter_row.numeric_value(col))
    filter_row.apply_invalid_numeric_columns(proxy.invalid_numeric_columns())


def bind_fm_filter_row(
    filter_row: TableFilterRowWidget,
    table: QTableView,
    proxy: TableColumnFilterProxy,
    *,
    on_filters_changed,
) -> None:
    filter_row.bind_header(table.horizontalHeader())

    def _push() -> None:
        apply_fm_filter_row_to_proxy(filter_row, proxy)
        on_filters_changed()

    filter_row.filters_changed.connect(_push)
