"""Slice 72 — Top 10 UX-verfijning (TDD)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QMessageBox

from rcm_core.effect_impact_service import EffectNbFilterSet
from rcm_desktop.adapter.contribution_chart_service import ContributionRow, build_contribution_rows
from rcm_desktop.adapter.contribution_display_service import (
    format_contribution_bar_annotation,
    format_contribution_value,
)
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_BIJDRAGEN,
    SOURCE_FAALWIJZE,
    SOURCE_PBS,
    ContributionPresentation,
    ResultsWorkspaceState,
)
from rcm_desktop.views.panels.bijdragen_workspace_panel import build_bijdragen_workspace_panel
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from rcm_desktop.views.widgets.contribution_bar_chart import ContributionBarChartWidget
from rcm_desktop.views.widgets.nb_effect_filter_combo import NbEffectFilterCombo

from tests.test_desktop_results_workspace_window import (
    _done_run_for_fixture,
    _ensure_app,
    _inject_run,
    _three_level_project,
)

CM_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_CM.xlsx"


# --- 00: NB-effectfilter popup ---


def test_nb_effect_filter_combo_click_opens_popup() -> None:
    _ensure_app()
    combo = NbEffectFilterCombo()
    combo.set_klassen((("EK-1", "Schutten"),))
    opened: list[bool] = []
    combo.showPopup = lambda: opened.append(True)  # type: ignore[method-assign]

    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPoint(5, 5),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    combo.mousePressEvent(event)

    assert opened == [True]


# --- 05: display-seam ---


def test_format_contribution_value_nb_hours() -> None:
    pres = ContributionPresentation(unavailability_display="hours")
    text = format_contribution_value(12.5, METRIC_NIET_BESCHIKBAARHEID, pres)
    assert "h" in text


def test_format_contribution_value_kosten() -> None:
    text = format_contribution_value(1500.0, METRIC_KOSTEN, ContributionPresentation())
    assert "€" in text


def test_format_contribution_bar_annotation_uses_value_not_share() -> None:
    pres = ContributionPresentation(unavailability_display="hours")
    text = format_contribution_bar_annotation(42.0, METRIC_NIET_BESCHIKBAARHEID, pres)
    assert "h" in text
    assert "%" not in text


# --- 03: chart labels ---


def test_chart_bar_label_follows_nb_hours_display() -> None:
    _ensure_app()
    widget = ContributionBarChartWidget()
    pres = ContributionPresentation(unavailability_display="hours")
    row = ContributionRow(category_id="FM-1", label="Test", value=10.5, share_pct=50.0)
    widget.set_display_context(METRIC_NIET_BESCHIKBAARHEID, pres)
    widget.set_rows((row,))

    label = widget.bar_value_label(row)
    assert "h" in label
    assert "%" not in label


def test_chart_bar_label_follows_kosten_metric() -> None:
    _ensure_app()
    widget = ContributionBarChartWidget()
    row = ContributionRow(category_id="FM-1", label="Test", value=2000.0, share_pct=30.0)
    widget.set_display_context(METRIC_KOSTEN, ContributionPresentation())
    widget.set_rows((row,))

    label = widget.bar_value_label(row)
    assert "€" in label


# --- 01: faalwijze default, no component toggle ---


def test_workspace_default_source_is_pbs() -> None:
    state = ResultsWorkspaceState()
    assert state.snapshot().source == SOURCE_PBS


def test_bijdragen_top10_has_no_component_source_toggle(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert not hasattr(window, "source_toggle_pbs_button")



# --- 02: chart-only ---


def test_bijdragen_panel_has_chart_without_table() -> None:
    _ensure_app()
    panel = build_bijdragen_workspace_panel()
    assert panel.chart_widget is not None
    assert not hasattr(panel, "table_view")


def test_bijdragen_compare_column_has_chart_without_table() -> None:
    _ensure_app()
    from rcm_desktop.views.compare_slot_column import build_bijdragen_compare_column

    col = build_bijdragen_compare_column()
    assert "chart" in col
    assert "table" not in col


# --- 04: NB filter e2e ---


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_top10_faalwijze_nb_filter_changes_ranking_values() -> None:
    from rcm_core.incremental_run import run_incremental_analysis
    from rcm_desktop.adapter.isograph_import_service import build_from_workbook
    from rcm_desktop.adapter.run_service import build_run_result

    result = build_from_workbook(CM_FIXTURE, modeljaar=2026)
    run_out = run_incremental_analysis(
        result.project,
        CM_FIXTURE.with_suffix(".rcm.cache.json"),
        full_recompute=True,
        parallel=False,
    )
    run = build_run_result(result.project, list(run_out.fm_results.values()))
    schutten = "Schutten 0-20% functieverlies"
    all_rows = build_contribution_rows(
        result.project,
        run,
        source=SOURCE_FAALWIJZE,
        metric=METRIC_NIET_BESCHIKBAARHEID,
        top_n=10,
        scope_id=None,
        effect_nb_filter=EffectNbFilterSet(),
    )
    filt_rows = build_contribution_rows(
        result.project,
        run,
        source=SOURCE_FAALWIJZE,
        metric=METRIC_NIET_BESCHIKBAARHEID,
        top_n=10,
        scope_id=None,
        effect_nb_filter=EffectNbFilterSet(selected_klasse_ids=frozenset({schutten})),
    )
    assert len(all_rows) >= 1
    assert len(filt_rows) >= 1
    assert sum(r.value for r in all_rows) != pytest.approx(
        sum(r.value for r in filt_rows), rel=0.01
    )


def test_chart_label_reflects_filtered_nb_value(monkeypatch) -> None:
    _ensure_app()
    widget = ContributionBarChartWidget()
    pres = ContributionPresentation(unavailability_display="hours")
    row = ContributionRow(category_id="FM-1", label="FM", value=7.25, share_pct=100.0)
    widget.set_display_context(METRIC_NIET_BESCHIKBAARHEID, pres)
    widget.set_rows((row,))

    label = widget.bar_value_label(row)
    assert format_contribution_value(7.25, METRIC_NIET_BESCHIKBAARHEID, pres) == label
