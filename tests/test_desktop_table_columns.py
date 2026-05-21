from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from rcm_desktop.table_columns import clamp_horizontal_section_widths, configure_horizontal_sections
from rcm_desktop.table_ui_constants import TEXT_COL_MAX_WIDTH_COMPACT, TEXT_COL_MAX_WIDTH_WIDE


def test_text_column_width_constants_ordered():
    assert TEXT_COL_MAX_WIDTH_COMPACT < TEXT_COL_MAX_WIDTH_WIDE
    assert TEXT_COL_MAX_WIDTH_COMPACT >= 200
    assert TEXT_COL_MAX_WIDTH_WIDE <= 1200


def test_configure_horizontal_sections_last_column_stretch_and_clamp():
    table = QTableWidget(2, 4)
    table.setHorizontalHeaderLabels(["a", "breed", "c", "d"])
    table.setItem(0, 1, QTableWidgetItem("x" * 80))
    header = table.horizontalHeader()
    header.setMinimumSectionSize(10)
    configure_horizontal_sections(header, column_count=4, stretch_last=True)
    assert header.sectionResizeMode(3) == QHeaderView.Stretch
    assert header.sectionResizeMode(0) == QHeaderView.ResizeToContents
    assert header.sectionResizeMode(1) == QHeaderView.ResizeToContents
    table.resizeColumnsToContents()
    assert header.sectionSize(1) > 72
    clamp_horizontal_section_widths(header, {1: 72})
    assert header.sectionSize(1) <= 72
