from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt

from rcm_desktop import messages
from rcm_desktop.adapter.pbs_results_table_model import PBSResultsTableModel
from rcm_desktop.adapter.result_view_service import PBSResultRow


def _row() -> PBSResultRow:
    return PBSResultRow(
        pbs_id="PBS-1",
        bouwdeel_naam="Pompkamer",
        parent_pbs_id=None,
        level=2,
        sort_path=("ROOT", "MID", "PBS-1"),
        expected_failures_self=2.0,
        total_downtime_hr_self=3.0,
        total_cost_eur_self=4.0,
        expected_failures_total=12.0,
        total_downtime_hr_total=1234.5,
        total_cost_eur_total=1200.0,
        unavailability_pct_total=9.5,
    )


def test_model_shape_and_headers():
    model = PBSResultsTableModel([_row()])
    assert model.rowCount() == 1
    assert model.columnCount() == 7
    assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == messages.PBS_RESULTS_HEADER_PBS_ID
    assert model.headerData(6, Qt.Horizontal, Qt.DisplayRole) == messages.PBS_RESULTS_HEADER_COST_TOTAL_EUR


def test_model_display_role_formats_values():
    model = PBSResultsTableModel([_row()])
    assert model.data(model.index(0, 1), Qt.DisplayRole) == "    Pompkamer"
    assert model.data(model.index(0, 2), Qt.DisplayRole) == "2"
    assert model.data(model.index(0, 3), Qt.DisplayRole) == "12"
    assert model.data(model.index(0, 4), Qt.DisplayRole) == "1.234,50"
    assert model.data(model.index(0, 5), Qt.DisplayRole) == "9,50%"
    assert model.data(model.index(0, 6), Qt.DisplayRole) == "€ 1.200,00"


def test_model_user_role_uses_raw_values_for_sorting():
    raw_role = Qt.UserRole + 1
    model = PBSResultsTableModel([_row()])
    assert model.data(model.index(0, 0), raw_role) == "PBS-1"
    assert model.data(model.index(0, 1), raw_role) == "Pompkamer"
    assert model.data(model.index(0, 2), raw_role) == 2
    assert model.data(model.index(0, 3), raw_role) == 12.0
    assert model.data(model.index(0, 4), raw_role) == 1234.5
    assert model.data(model.index(0, 5), raw_role) == 9.5
    assert model.data(model.index(0, 6), raw_role) == 1200.0
