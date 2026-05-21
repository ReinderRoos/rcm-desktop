"""QHeaderView helpers for capped text columns (slice 18)."""

from __future__ import annotations

from PySide6.QtWidgets import QHeaderView, QTableWidget

from rcm_desktop.table_ui_constants import TEXT_COL_MAX_WIDTH_WIDE


def effective_row_count(table: QTableWidget) -> int:
    return table.rowCount()


def resize_rows_if_wrapped_within_limit(
    table: QTableWidget,
    *,
    wrapped: bool,
    max_rows: int,
) -> None:
    if not wrapped or effective_row_count(table) > max_rows:
        return
    table.resizeRowsToContents()


def configure_horizontal_sections(
    header: QHeaderView,
    *,
    column_count: int,
    stretch_last: bool = True,
) -> None:
    for col in range(column_count):
        if stretch_last and col == column_count - 1:
            header.setSectionResizeMode(col, QHeaderView.Stretch)
        else:
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)


def clamp_horizontal_section_widths(
    header: QHeaderView,
    max_width_by_column: dict[int, int],
    *,
    default_max: int = TEXT_COL_MAX_WIDTH_WIDE,
) -> None:
    for col, max_w in max_width_by_column.items():
        cap = min(max_w, default_max)
        if header.sectionSize(col) > cap:
            header.resizeSection(col, cap)
