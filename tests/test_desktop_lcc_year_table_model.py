from __future__ import annotations

from PySide6.QtCore import Qt

from rcm_desktop.adapter.lcc_chart_service import LCCYearBucket
from rcm_desktop.adapter.lcc_year_table_model import (
    RAW_ROLE,
    LCCYearTableModel,
)


def test_empty_model_has_four_columns_and_zero_rows():
    model = LCCYearTableModel(())

    assert model.rowCount() == 0
    assert model.columnCount() == 4
    headers = [
        model.headerData(c, Qt.Horizontal, Qt.DisplayRole) for c in range(4)
    ]
    assert headers[0] == "Kalenderjaar"
    assert "Correctief" in headers[1]
    assert "Preventief" in headers[2]
    assert "Totaal" in headers[3]


def test_two_buckets_render_year_and_three_eur_columns():
    buckets = (
        LCCYearBucket(calendar_year=2025, correctief_eur=120.0, preventief_eur=80.0),
        LCCYearBucket(calendar_year=2026, correctief_eur=200.0, preventief_eur=50.0),
    )
    model = LCCYearTableModel(buckets)

    assert model.rowCount() == 2
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "2025"
    text_corr = model.data(model.index(0, 1), Qt.DisplayRole)
    assert "€" in text_corr and "120" in text_corr
    text_total = model.data(model.index(0, 3), Qt.DisplayRole)
    assert "200" in text_total  # 120 + 80


def test_raw_role_returns_numeric_values():
    buckets = (
        LCCYearBucket(calendar_year=2030, correctief_eur=10.0, preventief_eur=5.0),
    )
    model = LCCYearTableModel(buckets)

    assert model.data(model.index(0, 0), RAW_ROLE) == 2030
    assert model.data(model.index(0, 1), RAW_ROLE) == 10.0
    assert model.data(model.index(0, 2), RAW_ROLE) == 5.0
    assert model.data(model.index(0, 3), RAW_ROLE) == 15.0


def test_rows_are_sorted_ascending_on_calendar_year_regardless_of_input_order():
    buckets = (
        LCCYearBucket(calendar_year=2030, correctief_eur=0.0, preventief_eur=0.0),
        LCCYearBucket(calendar_year=2025, correctief_eur=0.0, preventief_eur=0.0),
        LCCYearBucket(calendar_year=2027, correctief_eur=0.0, preventief_eur=0.0),
    )
    model = LCCYearTableModel(buckets)

    years = [int(model.data(model.index(r, 0), RAW_ROLE)) for r in range(model.rowCount())]
    assert years == [2025, 2027, 2030]
