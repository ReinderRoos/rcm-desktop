from __future__ import annotations

from PySide6.QtCore import Qt

from rcm_desktop.adapter.contribution_chart_service import ContributionRow
from rcm_desktop.adapter.contribution_table_model import (
    RAW_ROLE,
    ContributionTableModel,
)
from rcm_desktop.adapter.results_workspace_state import (
    ContributionPresentation,
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
)


def test_contribution_table_model_exposes_categorie_waarde_aandeel_columns():
    model = ContributionTableModel(
        rows=(),
        metric=METRIC_KOSTEN,
    )

    assert model.columnCount() == 3
    headers = [
        model.headerData(c, Qt.Horizontal, Qt.DisplayRole) for c in range(3)
    ]
    assert headers[0] == "Categorie"
    assert "Aandeel" in headers[2]


def test_kosten_value_is_formatted_as_euro_and_share_as_percentage():
    rows = (
        ContributionRow(category_id="PBS-A", label="Pomp A", value=1500.0, share_pct=60.0),
        ContributionRow(category_id="PBS-B", label="Pomp B", value=1000.0, share_pct=40.0),
    )
    model = ContributionTableModel(rows=rows, metric=METRIC_KOSTEN)

    assert model.rowCount() == 2
    idx_label = model.index(0, 0)
    idx_value = model.index(0, 1)
    idx_share = model.index(0, 2)

    assert model.data(idx_label, Qt.DisplayRole) == "Pomp A"
    assert "€" in model.data(idx_value, Qt.DisplayRole)
    assert "1.500" in model.data(idx_value, Qt.DisplayRole)
    assert model.data(idx_share, Qt.DisplayRole).startswith("60")
    assert "%" in model.data(idx_share, Qt.DisplayRole)


def test_raw_role_returns_unformatted_numeric_value():
    rows = (
        ContributionRow(category_id="PBS-A", label="Pomp A", value=1234.5, share_pct=42.5),
    )
    model = ContributionTableModel(rows=rows, metric=METRIC_KOSTEN)

    assert model.data(model.index(0, 1), RAW_ROLE) == 1234.5
    assert model.data(model.index(0, 2), RAW_ROLE) == 42.5


def test_niet_beschikbaarheid_percent_formats_with_percent_sign():
    rows = (
        ContributionRow(category_id="PBS-A", label="Pomp A", value=0.1234, share_pct=80.0),
    )
    pres = ContributionPresentation(unavailability_display="percent")
    model = ContributionTableModel(
        rows=rows, metric=METRIC_NIET_BESCHIKBAARHEID, presentation=pres
    )

    text = model.data(model.index(0, 1), Qt.DisplayRole)
    assert "%" in text


def test_niet_beschikbaarheid_hours_formats_with_h_suffix():
    rows = (
        ContributionRow(category_id="PBS-A", label="Pomp A", value=12.5, share_pct=80.0),
    )
    pres = ContributionPresentation(unavailability_display="hours")
    model = ContributionTableModel(
        rows=rows, metric=METRIC_NIET_BESCHIKBAARHEID, presentation=pres
    )

    text = model.data(model.index(0, 1), Qt.DisplayRole)
    assert "h" in text


def test_faalmomenten_metric_rounds_value_to_integer_with_thousand_separators():
    rows = (
        ContributionRow(category_id="PBS-A", label="Pomp A", value=12345.4, share_pct=10.0),
    )
    model = ContributionTableModel(rows=rows, metric=METRIC_FAALMOMENTEN)

    text = model.data(model.index(0, 1), Qt.DisplayRole)
    assert text == "12.345"
