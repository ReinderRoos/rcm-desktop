from __future__ import annotations

from PySide6.QtCore import Qt

from rcm_desktop.adapter.pm_chart_service import PMYearRow
from rcm_desktop.adapter.pm_year_table_model import RAW_ROLE, PMYearTableModel
from rcm_desktop.adapter.pm_chart_service import (
    PM_SUBMODE_AANTAL_UITVOERINGEN,
    PM_SUBMODE_KOSTEN,
)


def test_kosten_submode_headers_and_eur_formatting():
    rows = (PMYearRow(calendar_year=2025, value=1500.0, cumulative=1500.0),)
    model = PMYearTableModel(rows, submode=PM_SUBMODE_KOSTEN)

    headers = [model.headerData(c, Qt.Horizontal, Qt.DisplayRole) for c in range(3)]
    assert headers[0] == "Kalenderjaar"
    assert "EUR" in headers[1]
    assert "EUR" in headers[2]

    text_val = model.data(model.index(0, 1), Qt.DisplayRole)
    assert "€" in text_val and "1.500" in text_val


def test_aantal_submode_headers_and_integer_formatting():
    rows = (PMYearRow(calendar_year=2025, value=7.0, cumulative=7.0),)
    model = PMYearTableModel(rows, submode=PM_SUBMODE_AANTAL_UITVOERINGEN)

    headers = [model.headerData(c, Qt.Horizontal, Qt.DisplayRole) for c in range(3)]
    assert headers[1] == "Aantal uitvoeringen"

    assert model.data(model.index(0, 1), Qt.DisplayRole) == "7"
    assert model.data(model.index(0, 2), Qt.DisplayRole) == "7"


def test_raw_role_returns_unformatted_values():
    rows = (PMYearRow(calendar_year=2030, value=42.0, cumulative=100.0),)
    model = PMYearTableModel(rows, submode=PM_SUBMODE_KOSTEN)

    assert model.data(model.index(0, 0), RAW_ROLE) == 2030
    assert model.data(model.index(0, 1), RAW_ROLE) == 42.0
    assert model.data(model.index(0, 2), RAW_ROLE) == 100.0


def test_rows_sorted_ascending_by_calendar_year():
    rows = (
        PMYearRow(calendar_year=2030, value=0.0, cumulative=0.0),
        PMYearRow(calendar_year=2025, value=0.0, cumulative=0.0),
    )
    model = PMYearTableModel(rows, submode=PM_SUBMODE_KOSTEN)

    years = [int(model.data(model.index(r, 0), RAW_ROLE)) for r in range(model.rowCount())]
    assert years == [2025, 2030]
