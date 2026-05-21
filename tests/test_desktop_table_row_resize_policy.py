from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QTableWidget

from rcm_desktop.table_columns import effective_row_count, resize_rows_if_wrapped_within_limit
from rcm_desktop.table_ui_constants import ROW_RESIZE_MAX_ROWS_LTAP_DETAIL


def test_effective_row_count_qtablewidget():
    app = QApplication.instance() or QApplication([])
    table = QTableWidget(5, 1)
    assert effective_row_count(table) == 5


def test_resize_rows_skipped_over_limit():
    app = QApplication.instance() or QApplication([])
    table = QTableWidget()
    table.setRowCount(ROW_RESIZE_MAX_ROWS_LTAP_DETAIL + 1)
    calls: list[int] = []

    def fake_resize() -> None:
        calls.append(1)

    table.resizeRowsToContents = fake_resize  # type: ignore[method-assign]
    resize_rows_if_wrapped_within_limit(
        table,
        wrapped=True,
        max_rows=ROW_RESIZE_MAX_ROWS_LTAP_DETAIL,
    )
    assert calls == []


def test_resize_rows_runs_under_limit():
    app = QApplication.instance() or QApplication([])
    table = QTableWidget()
    table.setRowCount(3)
    calls: list[int] = []

    def fake_resize() -> None:
        calls.append(1)

    table.resizeRowsToContents = fake_resize  # type: ignore[method-assign]
    resize_rows_if_wrapped_within_limit(table, wrapped=True, max_rows=500)
    assert calls == [1]


def test_resize_rows_skipped_when_wrap_off():
    app = QApplication.instance() or QApplication([])
    table = QTableWidget()
    table.setRowCount(2)
    calls: list[int] = []

    def fake_resize() -> None:
        calls.append(1)

    table.resizeRowsToContents = fake_resize  # type: ignore[method-assign]
    resize_rows_if_wrapped_within_limit(table, wrapped=False, max_rows=99999)
    assert calls == []
