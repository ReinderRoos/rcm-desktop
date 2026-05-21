from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from rcm_desktop import messages
from rcm_desktop.adapter.fm_results_table_model import (
    FMResultsSortProxy,
    FMResultsTableModel,
    RAW_ROLE,
)
from rcm_desktop.adapter.result_view_service import FMResultRow


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


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


def test_sort_proxy_orders_downtime_numerically_not_lexically():
    """373 uur moet vóór 131.939 uur — display-strings sorteren dat lexicografisch fout."""
    _ensure_app()
    rows = [
        _row("FM-HIGH", "a", "PBS-1", "B", 1.0, 131_939.02, 100.0),
        _row("FM-LOW", "b", "PBS-1", "B", 1.0, 373.08, 200.0),
        _row("FM-MID", "c", "PBS-1", "B", 1.0, 994.87, 300.0),
    ]
    source = FMResultsTableModel(rows)
    proxy = FMResultsSortProxy()
    proxy.setSourceModel(source)
    proxy.sort(5, Qt.AscendingOrder)

    ordered = [
        proxy.data(proxy.index(row, 0), RAW_ROLE) for row in range(proxy.rowCount())
    ]
    assert ordered == ["FM-LOW", "FM-MID", "FM-HIGH"]


def test_sort_proxy_orders_total_cost_numerically():
    _ensure_app()
    rows = [
        _row("FM-A", "a", "PBS-1", "B", 1.0, 1.0, 823_298.26),
        _row("FM-B", "b", "PBS-1", "B", 1.0, 1.0, 221_096.60),
    ]
    source = FMResultsTableModel(rows)
    proxy = FMResultsSortProxy()
    proxy.setSourceModel(source)
    proxy.sort(6, Qt.AscendingOrder)

    ordered = [
        proxy.data(proxy.index(row, 0), RAW_ROLE) for row in range(proxy.rowCount())
    ]
    assert ordered == ["FM-B", "FM-A"]
