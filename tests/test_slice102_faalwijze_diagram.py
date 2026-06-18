"""Slice 102-B2 — Faalwijze-analyse diagram in FM compare."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A, COMPARE_SLOT_B
from rcm_desktop.adapter.faalwijze_analyse_service import (
    FM_COMPARE_VIEW_DIAGRAM,
    FM_COMPARE_VIEW_TABLE,
    FaalwijzeComparePresentation,
    FaalwijzeCompareRow,
    FaalwijzeCompareSlotCell,
    build_faalwijze_compare_presentation,
)
from rcm_desktop.adapter.results_workspace_state import METRIC_FAALMOMENTEN, METRIC_KOSTEN
from rcm_desktop.adapter.results_workspace_orchestrator import (
    _plan_output_fm_results_toolbar,
    chrome_for_view,
)
from rcm_desktop.adapter.results_workspace_state import MODE_FM_DETAIL
from rcm_desktop.adapter.workspace_view_registry import WORKSPACE_VIEW_REGISTRY, chrome_for_view
from rcm_desktop.theme.dp_tokens import DP_SCENARIO_1, DP_SCENARIO_2, DP_WARNING_BG
from rcm_desktop.views.widgets.faalwijze_compare_bar_chart import FaalwijzeCompareBarChartWidget
from tests.test_desktop_results_workspace_window import _ensure_app
from tests.test_slice102_faalwijze_compare import _analytical_row, _panels


def _presentation(*rows: FaalwijzeCompareRow, metric: str = METRIC_FAALMOMENTEN) -> FaalwijzeComparePresentation:
    return FaalwijzeComparePresentation(rows=rows, metric=metric)


def test_fm_compare_view_mode_constants() -> None:
    assert FM_COMPARE_VIEW_TABLE == "table"
    assert FM_COMPARE_VIEW_DIAGRAM == "diagram"


def test_faalwijze_compare_bar_chart_row_order_matches_presentation() -> None:
    _ensure_app()
    pres = _presentation(
        FaalwijzeCompareRow(
            fm_id="fm-b",
            label="B",
            bouwdeel_naam="X",
            s1=20.0,
            s2=10.0,
            highlight=False,
            s1_cell=FaalwijzeCompareSlotCell(20.0),
            s2_cell=FaalwijzeCompareSlotCell(10.0),
        ),
        FaalwijzeCompareRow(
            fm_id="fm-a",
            label="A",
            bouwdeel_naam="X",
            s1=50.0,
            s2=40.0,
            highlight=True,
            s1_cell=FaalwijzeCompareSlotCell(50.0),
            s2_cell=FaalwijzeCompareSlotCell(40.0),
        ),
    )
    chart = FaalwijzeCompareBarChartWidget()
    chart.set_presentation(pres)
    assert chart.fm_ids_in_order() == ("fm-b", "fm-a")
    assert chart.highlighted_fm_ids() == ("fm-a",)


def test_faalwijze_compare_bar_chart_uses_scenario_colors() -> None:
    _ensure_app()
    chart = FaalwijzeCompareBarChartWidget()
    assert chart.scenario_color_s1() == QColor(DP_SCENARIO_1)
    assert chart.scenario_color_s2() == QColor(DP_SCENARIO_2)


def test_faalwijze_compare_bar_chart_preferred_height_scales_with_rows() -> None:
    _ensure_app()
    chart = FaalwijzeCompareBarChartWidget()
    chart.set_presentation(_presentation())
    empty_height = chart.preferred_height()
    rows = tuple(
        FaalwijzeCompareRow(
            fm_id=f"fm-{index}",
            label=f"FM {index}",
            bouwdeel_naam="X",
            s1=float(index),
            s2=float(index) + 1.0,
            highlight=False,
            s1_cell=FaalwijzeCompareSlotCell(float(index)),
            s2_cell=FaalwijzeCompareSlotCell(float(index) + 1.0),
        )
        for index in range(8)
    )
    chart.set_presentation(_presentation(*rows))
    assert chart.preferred_height() > empty_height


def test_faalwijze_compare_bar_chart_highlight_background() -> None:
    _ensure_app()
    chart = FaalwijzeCompareBarChartWidget()
    assert chart.row_background_color(highlight=True) == QColor(DP_WARNING_BG)
    assert chart.row_background_color(highlight=False) is None


def test_fm_toolbar_shows_view_toggle_in_compare_mode() -> None:
    from dataclasses import replace

    from rcm_desktop.adapter.results_workspace_state import ResultsWorkspaceState

    state = ResultsWorkspaceState()
    state.set_compare_mode(True)
    snapshot = replace(state.snapshot(), modus=MODE_FM_DETAIL)
    profile = chrome_for_view(WORKSPACE_VIEW_REGISTRY, snapshot.active_view_id)
    assert profile is not None
    toolbar = _plan_output_fm_results_toolbar(snapshot, profile)
    assert toolbar.fm_compare_view_toggle_visible is True


def test_fm_toolbar_shows_view_toggle_in_output_fm() -> None:
    from rcm_desktop.adapter.results_workspace_state import ResultsWorkspaceState

    state = ResultsWorkspaceState()
    snapshot = state.snapshot()
    profile = chrome_for_view(WORKSPACE_VIEW_REGISTRY, snapshot.active_view_id)
    assert profile is not None
    toolbar = _plan_output_fm_results_toolbar(snapshot, profile)
    assert toolbar.fm_compare_view_toggle_visible is True


def test_window_fm_compare_defaults_to_table_view(monkeypatch) -> None:
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    assert window._fm_bind.view_mode == FM_COMPARE_VIEW_TABLE
    assert window.fm_compare_table_view_button.isChecked()
    assert window.fm_compare_columns_host.isVisible() is False
    assert window.fm_compare_chart_scroll.isVisible() is False


def test_window_fm_compare_switch_to_diagram(monkeypatch) -> None:
    from dataclasses import replace

    from rcm_desktop.adapter.results_workspace_state import ResultsWorkspaceState
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    panels = _panels(
        (_analytical_row("fm-a", failures=120.0, label="Pomp"),),
        (_analytical_row("fm-a", failures=80.0, label="Pomp"),),
    )
    state = ResultsWorkspaceState()
    state.set_compare_mode(True)
    snapshot = replace(state.snapshot(), modus=MODE_FM_DETAIL)
    pres = build_faalwijze_compare_presentation(panels, metric=METRIC_FAALMOMENTEN)
    from rcm_desktop.adapter.faalwijze_analyse_service import FaalwijzePresentationBundle
    from rcm_desktop.views.panels import fm_detail_workspace_binding as binding

    binding.apply_fm_compare_panels(
        window,
        panels,
        snapshot,
        bundle=FaalwijzePresentationBundle(compare=pres),
    )
    window.fm_compare_pane.setVisible(True)
    window.fm_compare_chart_scroll.resize(640, 480)
    window._fm_bind.set_view_mode(FM_COMPARE_VIEW_DIAGRAM)
    assert window._fm_bind.view_mode == FM_COMPARE_VIEW_DIAGRAM
    assert window.fm_compare_diagram_view_button.isChecked()
    assert window.fm_compare_nmf_rf_toggle.isVisible() is False
    assert len(window.fm_compare_chart.fm_ids_in_order()) >= 1
    assert window.fm_compare_chart.height() >= window.fm_compare_chart.preferred_height()
    assert window.fm_compare_chart.width() >= 360


def test_build_presentation_metric_switch_updates_chart_metric_label() -> None:
    panels = _panels()
    failures = build_faalwijze_compare_presentation(panels, metric=METRIC_FAALMOMENTEN)
    costs = build_faalwijze_compare_presentation(panels, metric=METRIC_KOSTEN)
    _ensure_app()
    chart = FaalwijzeCompareBarChartWidget()
    chart.set_presentation(failures)
    assert chart.active_metric() == METRIC_FAALMOMENTEN
    chart.set_presentation(costs)
    assert chart.active_metric() == METRIC_KOSTEN
