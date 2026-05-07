from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt

from rcm_desktop import messages
from rcm_desktop.adapter.fm_results_table_model import FMResultsTableModel
from rcm_desktop.adapter.result_view_service import FMResultRow


def _row(
    fm_id: str,
    omschrijving: str,
    pbs_id: str,
    bouwdeel_naam: str,
    expected_failures: float,
    expected_total_downtime_hr: float,
    total_cost_eur: float,
) -> FMResultRow:
    return FMResultRow(
        fm_id=fm_id,
        faalwijze_omschrijving=omschrijving,
        pbs_id=pbs_id,
        bouwdeel_naam=bouwdeel_naam,
        expected_failures=expected_failures,
        expected_total_downtime_hr=expected_total_downtime_hr,
        total_cost_eur=total_cost_eur,
    )


def test_model_shape_and_headers():
    model = FMResultsTableModel([_row("FM-1", "omschrijving", "PBS-1", "Bouwdeel", 1.2, 3.4, 1200.0)])

    assert model.rowCount() == 1
    assert model.columnCount() == 7
    assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == messages.FM_RESULTS_HEADER_FM_ID
    assert model.headerData(6, Qt.Horizontal, Qt.DisplayRole) == messages.FM_RESULTS_HEADER_TOTAL_COST_EUR


def test_model_display_role_formats_values_for_ui():
    model = FMResultsTableModel([_row("FM-1", "omschrijving", "PBS-1", "Bouwdeel", 12.0, 1234.5, 1200.0)])

    assert model.data(model.index(0, 4), Qt.DisplayRole) == "12"
    assert model.data(model.index(0, 5), Qt.DisplayRole) == "1.234,50"
    assert model.data(model.index(0, 6), Qt.DisplayRole) == "€ 1.200,00"


def test_model_user_role_keeps_raw_values_for_sorting():
    model = FMResultsTableModel([_row("FM-1", "omschrijving", "PBS-1", "Bouwdeel", 12.0, 1234.5, 1200.0)])
    raw_role = Qt.UserRole + 1

    assert model.data(model.index(0, 4), raw_role) == 12.0
    assert model.data(model.index(0, 5), raw_role) == 1234.5
    assert model.data(model.index(0, 6), raw_role) == 1200.0
    assert model.data(model.index(0, 0), raw_role) == "FM-1"
