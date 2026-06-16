"""Slice 102-A — scenario-kleur in scenariovergelijking."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A, COMPARE_SLOT_B
from rcm_desktop.adapter.scenario_compare_chrome import (
    compare_header_stylesheet,
    scenario_color_hex,
)
from rcm_desktop.theme.dp_tokens import DP_SCENARIO_1, DP_SCENARIO_2
from rcm_desktop.views.widgets.contribution_bar_chart import ContributionBarChartWidget
from rcm_desktop.views.widgets.lcc_stacked_bar_chart import LCCStackedBarChartWidget
from tests.test_desktop_results_workspace_window import _ensure_app


def test_scenario_color_hex_maps_slots() -> None:
    assert scenario_color_hex(COMPARE_SLOT_A) == DP_SCENARIO_1
    assert scenario_color_hex(COMPARE_SLOT_B) == DP_SCENARIO_2


def test_compare_header_stylesheet_uses_scenario_color() -> None:
    assert DP_SCENARIO_1 in compare_header_stylesheet(COMPARE_SLOT_A)
    assert DP_SCENARIO_2 in compare_header_stylesheet(COMPARE_SLOT_B)


def test_contribution_chart_accepts_scenario_bar_color() -> None:
    app = _ensure_app()
    chart = ContributionBarChartWidget()
    chart.set_bar_color_hex(DP_SCENARIO_1)
    assert chart._bar_color_hex == DP_SCENARIO_1
    chart.set_bar_color_hex(None)
    assert chart._bar_color_hex is None


def test_lcc_chart_scenario_palette_overrides_stack_colors() -> None:
    app = _ensure_app()
    chart = LCCStackedBarChartWidget()
    default = chart._stack_colors()
    chart.set_scenario_palette(DP_SCENARIO_2)
    primary = chart._stack_colors()[1]
    assert primary == QColor(DP_SCENARIO_2)
    assert default != chart._stack_colors()
    chart.set_scenario_palette(None)
    assert chart._stack_colors() == default


def test_apply_compare_column_chrome_on_workspace_columns(monkeypatch) -> None:
    from PySide6.QtWidgets import QMessageBox

    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    window._apply_compare_column_chrome(window._bijdragen_compare_col_a, COMPARE_SLOT_A)
    window._apply_compare_column_chrome(window._fm_compare_col_b, COMPARE_SLOT_B)
    assert DP_SCENARIO_1 in window._bijdragen_compare_col_a["header"].styleSheet()
    assert DP_SCENARIO_2 in window._fm_compare_col_b["header"].styleSheet()
