"""Slice 105 issue 07 — LCC as-labels met eenheden."""

from __future__ import annotations

from rcm_desktop.adapter.lcc_plot_axis_labels import lcc_plot_axis_labels
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
)


def test_lcc_axis_labels_include_per_year_units() -> None:
    _, y_fm = lcc_plot_axis_labels(METRIC_FAALMOMENTEN)
    _, y_nb_h = lcc_plot_axis_labels(METRIC_NIET_BESCHIKBAARHEID, unavailability_display="hours")
    _, y_nb_pct = lcc_plot_axis_labels(
        METRIC_NIET_BESCHIKBAARHEID, unavailability_display="percent"
    )
    _, y_cost = lcc_plot_axis_labels(METRIC_KOSTEN)
    assert "/jaar" in y_fm
    assert "/jaar" in y_nb_h
    assert "/jaar" in y_nb_pct
    assert "€" in y_cost and "/jaar" in y_cost


def test_lcc_chart_calendar_year_at_matches_layout_metrics_arity() -> None:
    """Regression: slice 105 y_title_width — click handler must unpack 8 layout values."""
    import sys

    import pytest

    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from rcm_desktop.adapter.lcc_chart_service import LCCYearBucket
    from rcm_desktop.views.widgets.lcc_stacked_bar_chart import LCCStackedBarChartWidget

    app = QApplication.instance() or QApplication(sys.argv)
    chart = LCCStackedBarChartWidget()
    chart.resize(800, 300)
    chart.set_buckets(
        (
            LCCYearBucket(calendar_year=2026, correctief_eur=10.0, preventief_eur=5.0),
            LCCYearBucket(calendar_year=2027, correctief_eur=20.0, preventief_eur=0.0),
        )
    )
    assert chart._calendar_year_at(200, 100) == 2026
