"""Slice 71 post-fix — NB-effectfilter UI, cache, KPI-inklap."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QMessageBox

from rcm_core.effect_impact_service import EffectNbFilterSet
from rcm_desktop.adapter.presentation_cache_service import PresentationProjectTotal
from rcm_desktop.adapter.results_workspace_orchestrator import ResultsWorkspaceOrchestrator
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    MODE_LCC,
    ContributionPresentation,
    ResultsWorkspaceState,
)
from rcm_desktop.adapter.workspace_view_service import _contribution_cache_matches
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from rcm_desktop.views.widgets.nb_effect_filter_combo import NbEffectFilterCombo

from tests.test_desktop_results_workspace_window import (
    _ensure_app,
    _inject_run,
    _three_level_project,
)
from tests.test_results_workspace_orchestrator import _snap


def test_nb_effect_filter_combo_set_klassen_populates_model() -> None:
    _ensure_app()
    combo = NbEffectFilterCombo()
    klassen = (("EK-1", "Schutten"), ("EK-2", "Keren"))
    combo.set_klassen(klassen)

    model = combo.model()
    assert isinstance(model, QStandardItemModel)
    assert model.rowCount() == 2
    assert model.item(0).text() == "Schutten"
    assert model.item(0).data(Qt.UserRole) == "EK-1"
    assert combo.currentText() == "Alle NB-effecten"


def test_nb_effect_filter_combo_toggle_emits_filter() -> None:
    _ensure_app()
    combo = NbEffectFilterCombo()
    combo.set_klassen((("EK-1", "Schutten"), ("EK-2", "Keren")))
    seen: list[EffectNbFilterSet] = []
    combo.filter_changed.connect(seen.append)

    model = combo.model()
    assert isinstance(model, QStandardItemModel)
    item = model.item(0)
    assert item is not None
    assert item.checkState() == Qt.Unchecked
    combo._on_item_pressed(model.indexFromItem(item))

    assert len(seen) == 1
    assert seen[0].selected_klasse_ids == frozenset({"EK-1"})


def test_contribution_cache_misses_when_nb_filter_differs() -> None:
    pres = ContributionPresentation()
    cached = PresentationProjectTotal(
        contribution_source="pbs",
        contribution_metric=METRIC_NIET_BESCHIKBAARHEID,
        contribution_top_n=10,
        contribution_presentation=pres,
        contribution_rows=(),
    )
    snap = _snap(
        modus=MODE_BIJDRAGEN,
        metric=METRIC_NIET_BESCHIKBAARHEID,
        scope_id=None,
        contribution_presentation=pres,
        effect_nb_filter=EffectNbFilterSet(selected_klasse_ids=frozenset({"EK-1"})),
    )
    assert _contribution_cache_matches(snap, cached) is False


def test_kpi_collapse_plan_in_bijdragen_and_fm_detail() -> None:
    bijdragen = _snap(modus=MODE_BIJDRAGEN)
    plan_b = ResultsWorkspaceOrchestrator.plan_ui_sync(None, bijdragen)
    assert plan_b.collapse.kpi is not None
    assert plan_b.collapse.kpi.chrome_visible is True

    fm = _snap(modus=MODE_FM_DETAIL)
    plan_fm = ResultsWorkspaceOrchestrator.plan_ui_sync(None, fm)
    assert plan_fm.collapse.kpi is not None
    assert plan_fm.collapse.kpi.chrome_visible is True


def test_kpi_collapse_state_survives_modus_switch() -> None:
    state = ResultsWorkspaceState()
    state.set_modus(MODE_BIJDRAGEN)
    state.set_kpi_collapsed_in_lcc(True)
    state.set_modus(MODE_LCC)
    assert state.snapshot().kpi_collapsed_in_lcc is True


def test_kpi_collapse_hides_table_in_bijdragen_modus(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    app.processEvents()

    window.workspace_state.set_modus(MODE_BIJDRAGEN)
    window.workspace_state.set_kpi_collapsed_in_lcc(True)
    app.processEvents()

    kpi_action = window._workspace_menu.actions_by_id["view.kpi_overview_visible"]
    assert kpi_action.isVisible() is True
    assert window.kpi_table_view.isVisible() is False

    kpi_action.setChecked(True)
    app.processEvents()

    assert window.kpi_table_view.isVisible() is True
