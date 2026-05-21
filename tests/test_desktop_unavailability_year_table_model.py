from __future__ import annotations

from PySide6.QtCore import Qt

from rcm_desktop.adapter.unavailability_chart_service import UnavailabilityYearRow
from rcm_desktop.adapter.unavailability_year_table_model import (
    RAW_ROLE,
    UnavailabilityYearTableModel,
)


def test_empty_model_exposes_three_columns_and_zero_rows():
    model = UnavailabilityYearTableModel(())

    assert model.rowCount() == 0
    assert model.columnCount() == 3
    headers = [model.headerData(c, Qt.Horizontal, Qt.DisplayRole) for c in range(3)]
    assert headers[0] == "Kalenderjaar"
    assert "%" in headers[1]
    assert "uur" in headers[2].lower()


def test_rows_render_year_pct_and_downtime():
    rows = (
        UnavailabilityYearRow(calendar_year=2027, unavailability_pct=0.5, downtime_hr=43.8),
        UnavailabilityYearRow(calendar_year=2028, unavailability_pct=0.1, downtime_hr=8.76),
    )
    model = UnavailabilityYearTableModel(rows)

    assert model.rowCount() == 2
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "2027"
    pct_text = model.data(model.index(0, 1), Qt.DisplayRole)
    assert "%" in pct_text and pct_text.startswith("0,")
    hr_text = model.data(model.index(0, 2), Qt.DisplayRole)
    assert "43" in hr_text


def test_raw_role_returns_numeric_values():
    rows = (
        UnavailabilityYearRow(calendar_year=2030, unavailability_pct=0.2, downtime_hr=17.52),
    )
    model = UnavailabilityYearTableModel(rows)

    assert model.data(model.index(0, 0), RAW_ROLE) == 2030
    assert model.data(model.index(0, 1), RAW_ROLE) == 0.2
    assert model.data(model.index(0, 2), RAW_ROLE) == 17.52


def test_rows_are_sorted_ascending_by_calendar_year():
    rows = (
        UnavailabilityYearRow(calendar_year=2030, unavailability_pct=0.0, downtime_hr=0.0),
        UnavailabilityYearRow(calendar_year=2025, unavailability_pct=0.0, downtime_hr=0.0),
        UnavailabilityYearRow(calendar_year=2027, unavailability_pct=0.0, downtime_hr=0.0),
    )
    model = UnavailabilityYearTableModel(rows)

    years = [int(model.data(model.index(r, 0), RAW_ROLE)) for r in range(model.rowCount())]
    assert years == [2025, 2027, 2030]
