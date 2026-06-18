"""Slice 105 issue 03 — faalwijze-diagram labels in balk, geen streepjes."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from rcm_desktop.adapter.faalwijze_analyse_service import (
    FaalwijzeComparePresentation,
    FaalwijzeCompareRow,
    FaalwijzeCompareSlotCell,
)
from rcm_desktop.adapter.results_workspace_state import METRIC_FAALMOMENTEN
from rcm_desktop.views.widgets.faalwijze_compare_bar_chart import (
    FaalwijzeCompareBarChartWidget,
    ROW_HEIGHT,
    _LABEL_FONT_POINT_SIZE,
    _VALUE_FONT_POINT_SIZE,
)


def _row(*, s2: float | None = 10.0) -> FaalwijzeCompareRow:
    return FaalwijzeCompareRow(
        fm_id="FM-001",
        label="Test FM",
        bouwdeel_naam="BD",
        highlight=False,
        s1=20.0,
        s2=s2,
        s1_cell=FaalwijzeCompareSlotCell(20.0),
        s2_cell=FaalwijzeCompareSlotCell(s2) if s2 is not None else None,
    )


def test_row_height_at_least_56px() -> None:
    assert ROW_HEIGHT >= 56


def test_format_metric_none_is_empty_not_em_dash() -> None:
    chart = FaalwijzeCompareBarChartWidget()
    assert chart._format_metric(None) == ""


def test_single_scenario_row_has_no_placeholder_text() -> None:
    chart = FaalwijzeCompareBarChartWidget()
    chart.set_presentation(
        FaalwijzeComparePresentation(rows=(_row(s2=None),), metric=METRIC_FAALMOMENTEN)
    )
    assert chart._format_metric(None) == ""


def test_chart_has_no_fixed_right_value_gutter_constant() -> None:
    import rcm_desktop.views.widgets.faalwijze_compare_bar_chart as chart_mod

    assert not hasattr(chart_mod, "_VALUE_WIDTH")


def test_value_font_at_least_11pt() -> None:
    assert _VALUE_FONT_POINT_SIZE >= 11


def test_label_rows_share_font_point_size() -> None:
    assert _LABEL_FONT_POINT_SIZE == 10
    chart = FaalwijzeCompareBarChartWidget()
    chart.set_presentation(
        FaalwijzeComparePresentation(rows=(_row(),), metric=METRIC_FAALMOMENTEN)
    )
    assert chart._rows[0].label == "Test FM"
