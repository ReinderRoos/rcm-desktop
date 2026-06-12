"""Slice 82 — LTAP als preset-view op het LCC-panel."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_core.models import RCMProject

from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.results_workspace_orchestrator import ResultsWorkspaceOrchestrator
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_KOSTEN,
    MODE_LCC,
    ResultsWorkspaceState,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.run_service import run as run_single
from rcm_desktop.adapter.workspace_lcc_preset_service import effective_lcc_filters
from rcm_desktop.adapter.workspace_view_registry import (
    WORKSPACE_VIEW_REGISTRY,
    LccViewPreset,
    _LEGACY_MODUS_LCC,
    view_by_id,
)
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import _ensure_app

FIXTURE = Path("tests/fixtures/one_fm_planning.rcm.json")


def _snap(**kwargs) -> WorkspaceStateSnapshot:
    base = ResultsWorkspaceState().snapshot()
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    data.update(kwargs)
    return WorkspaceStateSnapshot(**data)


def _open_lcc_with_run(window: ResultsWorkspaceWindow, monkeypatch) -> None:
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    project = RCMProject.from_dict(json.loads(FIXTURE.read_text(encoding="utf-8")))
    window._state.set_last_project(project)
    rr = run_single(project, FIXTURE, full_recompute=True, parallel=False)
    assert rr.status == "done"
    window._state.set_last_run(rr)
    window.show()
    window.workspace_state.set_active_view("output.lcc_plot")
    window.workspace_state.set_metric(METRIC_KOSTEN)
    window.workspace_state.set_lcc_whatif_collapsed_in_lcc(False)
    window._rerender_detail_for_current_scope()


def test_ltap_registry_entry_enabled_with_cm_preset() -> None:
    entry = view_by_id(WORKSPACE_VIEW_REGISTRY, "output.ltap")
    assert entry is not None
    assert entry.enabled is True
    assert entry.legacy_modus == _LEGACY_MODUS_LCC
    assert entry.lcc_preset == LccViewPreset(cm_enabled=False)


def test_ltap_orchestrator_plan_excludes_cm_and_hides_cm_controls() -> None:
    snap = _snap(
        modus=MODE_LCC,
        active_view_id="output.ltap",
        metric=METRIC_KOSTEN,
        lcc_filters=LCCTypeFilterSet.all_on(),
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert plan.lcc_toolbar is not None
    assert plan.lcc_toolbar.lcc_filters.cm is False
    assert plan.lcc_toolbar.cm_filter_visible is False
    assert plan.lcc_toolbar.cm_preset_button_visible is False


def test_effective_lcc_filters_leaves_state_when_not_ltap() -> None:
    filters = LCCTypeFilterSet(cm=True, rev=False)
    snap = _snap(
        modus=MODE_LCC,
        active_view_id="output.lcc_plot",
        lcc_filters=filters,
    )
    assert effective_lcc_filters(snap) == filters


def test_set_active_view_ltap_does_not_mutate_stored_lcc_filters() -> None:
    state = ResultsWorkspaceState()
    state.set_active_view("output.lcc_plot")
    state.set_lcc_filters(LCCTypeFilterSet(cm=True, rev=True))
    state.set_active_view("output.ltap")
    assert state.snapshot().lcc_filters.cm is True
    assert state.snapshot().active_view_id == "output.ltap"


def test_switch_ltap_to_lcc_plot_restores_cm_filter_in_toolbar_plan() -> None:
    filters = LCCTypeFilterSet(cm=True, rev=True)
    ltap = _snap(
        modus=MODE_LCC,
        active_view_id="output.ltap",
        metric=METRIC_KOSTEN,
        lcc_filters=filters,
    )
    lcc_plot = _snap(
        modus=MODE_LCC,
        active_view_id="output.lcc_plot",
        metric=METRIC_KOSTEN,
        lcc_filters=filters,
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(ltap, lcc_plot)
    assert plan.lcc_toolbar is not None
    assert plan.lcc_toolbar.lcc_filters.cm is True
    assert plan.lcc_toolbar.cm_filter_visible is True


def test_ltap_hides_cm_controls_and_zeros_correctief(monkeypatch) -> None:
    app = _ensure_app()
    window = ResultsWorkspaceWindow()
    _open_lcc_with_run(window, monkeypatch)
    app.processEvents()

    lcc_cm_sum = sum(b.correctief_eur for b in window.lcc_chart_widget.buckets())
    assert lcc_cm_sum > 0.0
    assert window._lcc_filter_checks["cm"].isVisible() is True

    window.workspace_state.set_active_view("output.ltap")
    window.workspace_state.set_lcc_whatif_collapsed_in_lcc(False)
    app.processEvents()

    assert window._lcc_filter_checks["cm"].isVisible() is False
    assert window._lcc_filter_checks["cm"].isEnabled() is False
    assert window.lcc_cm_preset_button.isVisible() is False
    ltap_cm_sum = sum(b.correctief_eur for b in window.lcc_chart_widget.buckets())
    assert ltap_cm_sum == 0.0


def test_ltap_to_lcc_plot_restores_cm_checkbox(monkeypatch) -> None:
    app = _ensure_app()
    window = ResultsWorkspaceWindow()
    _open_lcc_with_run(window, monkeypatch)
    app.processEvents()

    window.workspace_state.set_active_view("output.ltap")
    window.workspace_state.set_lcc_whatif_collapsed_in_lcc(False)
    app.processEvents()
    assert window._lcc_filter_checks["cm"].isChecked() is False

    window.workspace_state.set_active_view("output.lcc_plot")
    window.workspace_state.set_lcc_whatif_collapsed_in_lcc(False)
    app.processEvents()
    assert window._lcc_filter_checks["cm"].isChecked() is True
    assert window._lcc_filter_checks["cm"].isVisible() is True
