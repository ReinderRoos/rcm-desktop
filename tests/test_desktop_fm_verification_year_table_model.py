from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt

from rcm_desktop import messages
from rcm_desktop.adapter.fm_verification_service import FMVerificationYearRow
from rcm_desktop.adapter.fm_verification_year_table_model import (
    FMVerificationYearTableModel,
)


def test_fm_verification_year_table_model_headers_and_display():
    rows = (
        FMVerificationYearRow(
            calendar_year=2020,
            faalmomenten=0.5,
            cor_eur=20.0,
            cor_downtime_hr=2.0,
            hidden_nb_hr=0.1,
        ),
    )
    model = FMVerificationYearTableModel(rows)
    assert model.columnCount() == 5
    assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == (
        messages.WORKSPACE_FM_INSPECTOR_YEAR_HEADER_KALENDERJAAR
    )
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "2020"
    assert "0,50" in str(model.data(model.index(0, 1), Qt.DisplayRole))
