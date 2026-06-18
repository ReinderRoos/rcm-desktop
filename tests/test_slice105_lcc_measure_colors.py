"""Slice 105 issue 08 — LCC maatregeltype-kleuren."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtGui import QColor

from rcm_desktop.theme.dp_tokens import DP_MEASURE_CM, DP_MEASURE_PM
from rcm_desktop.views.widgets.lcc_stacked_bar_chart import LCCStackedBarChartWidget


def test_lcc_stack_colors_use_delta_pi_tokens() -> None:
    chart = LCCStackedBarChartWidget()
    cm, pm = chart._stack_colors()
    assert cm == QColor(DP_MEASURE_CM)
    assert pm == QColor(DP_MEASURE_PM)
    assert cm != pm
