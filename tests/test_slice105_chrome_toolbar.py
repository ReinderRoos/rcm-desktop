"""Slice 105 issue 12 — chrome-profiel declarative toolbar."""

from __future__ import annotations

import pytest

from rcm_desktop.adapter.results_workspace_orchestrator import (
    LccToolbarVisibilityPlan,
    ResultsWorkspaceOrchestrator,
    plan_chrome_toolbar,
)
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_FM_DETAIL,
    MODE_LCC,
    ResultsWorkspaceState,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.workspace_view_registry import (
    SIDE_INPUT,
    SIDE_OUTPUT,
    WORKSPACE_VIEW_REGISTRY,
    chrome_for_view,
)


def _snap(**kwargs) -> WorkspaceStateSnapshot:
    base = ResultsWorkspaceState().snapshot()
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    data.update(kwargs)
    return WorkspaceStateSnapshot(**data)


def test_lcc_chrome_profile_declares_contribution_subbar() -> None:
    profile = chrome_for_view(WORKSPACE_VIEW_REGISTRY, "output.lcc_plot")
    assert profile is not None
    assert profile.shows_lcc_contribution_subbar is True


def test_fm_output_chrome_profile_declares_compare_toggles() -> None:
    profile = chrome_for_view(WORKSPACE_VIEW_REGISTRY, "output.fm_results")
    assert profile is not None
    assert profile.shows_fm_compare_toggles is True
    assert profile.shows_fm_inspector is True


def test_plan_chrome_toolbar_returns_lcc_plan_for_lcc_view() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.lcc_plot",
        modus=MODE_LCC,
        metric=METRIC_KOSTEN,
    )
    plan = plan_chrome_toolbar(snap)
    assert isinstance(plan, LccToolbarVisibilityPlan)
    assert plan.contribution_subbar_visible is True
    assert plan.pm_type_filters_visible is True


def test_orchestrator_lcc_toolbar_from_chrome_not_modus_only() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.lcc_plot",
        modus=MODE_LCC,
        metric=METRIC_NIET_BESCHIKBAARHEID,
    )
    ui = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert ui.lcc_toolbar is not None
    assert ui.lcc_toolbar.contribution_subbar_visible is True
    assert ui.lcc_toolbar.nb_display_toggles_visible is True


def test_orchestrator_fm_toolbar_horizon_from_chrome_profile() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.fm_results",
        modus=MODE_FM_DETAIL,
    )
    ui = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert ui.fm_toolbar is not None
    assert ui.fm_toolbar.horizon_lifecycle_visible is True
    assert ui.fm_toolbar.fm_compare_view_toggle_visible is True


def test_orchestrator_top10_subbar_hidden_on_input_faalwijzen() -> None:
    snap = _snap(
        workspace_side=SIDE_INPUT,
        active_view_id="input.faalwijzen",
        modus=MODE_FM_DETAIL,
    )
    ui = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert ui.top10_subbar_visible is False


def test_orchestrator_status_strip_hidden_on_input_faalwijzen() -> None:
    snap = _snap(
        workspace_side=SIDE_INPUT,
        active_view_id="input.faalwijzen",
        modus=MODE_FM_DETAIL,
    )
    ui = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert ui.status_strip_visible is False


def test_orchestrator_status_strip_hidden_on_output_fm_results() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.fm_results",
        modus=MODE_FM_DETAIL,
    )
    ui = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert ui.status_strip_visible is False


def test_status_strip_hidden_after_clicking_input_side(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QMessageBox

    from rcm_desktop.adapter.workspace_view_registry import SIDE_INPUT
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
    from tests.test_desktop_results_workspace_window import _ensure_app

    app = _ensure_app()
    from unittest.mock import patch

    with patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok):
        window = ResultsWorkspaceWindow()
        window.show()
        window._workspace_navigation.side_buttons[SIDE_INPUT].click()
        app.processEvents()
        assert window.workspace_state.snapshot().workspace_side == SIDE_INPUT
        assert window.status_strip.isVisible() is False
        assert window.status_strip.height() == 0


def test_orchestrator_top10_subbar_hidden_on_output_fm_results() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.fm_results",
        modus=MODE_FM_DETAIL,
    )
    ui = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert ui.top10_subbar_visible is False
    assert ui.fm_toolbar is not None
    assert ui.fm_toolbar.metric_combo_visible is True


def test_top10_subbar_hidden_on_output_fm_results_window(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QMessageBox

    from rcm_desktop.adapter.workspace_view_registry import SIDE_OUTPUT
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
    from tests.test_desktop_results_workspace_window import _ensure_app

    app = _ensure_app()
    from unittest.mock import patch

    with patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok):
        window = ResultsWorkspaceWindow()
        window.show()
        window.workspace_state.set_workspace_side(SIDE_OUTPUT)
        window.workspace_state.set_active_view("output.fm_results")
        app.processEvents()
        assert window.top10_subbar.isVisible() is False
        assert window.top10_subbar.height() == 0
        assert window.metric_combo.isVisible() is True
        assert window.metric_combo.parent() is window.fm_metric_chrome_host


def test_top10_subbar_hidden_after_clicking_input_side(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QMessageBox

    from rcm_desktop.adapter.workspace_view_registry import SIDE_INPUT
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
    from tests.test_desktop_results_workspace_window import _ensure_app

    app = _ensure_app()
    from unittest.mock import patch

    with patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok):
        window = ResultsWorkspaceWindow()
        window.show()
        window._workspace_navigation.side_buttons[SIDE_INPUT].click()
        app.processEvents()
        assert window.workspace_state.snapshot().workspace_side == SIDE_INPUT
        assert window.top10_subbar.isVisible() is False
        assert window.top10_subbar.height() == 0


def test_run_mode_combo_visible_on_input_side(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QMessageBox

    from rcm_desktop.adapter.workspace_view_registry import SIDE_INPUT
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
    from tests.test_desktop_results_workspace_window import _ensure_app

    app = _ensure_app()
    from unittest.mock import patch

    with patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok):
        window = ResultsWorkspaceWindow()
        window.show()
        window._workspace_navigation.side_buttons[SIDE_INPUT].click()
        app.processEvents()
        assert window.status_strip.isVisible() is False
        assert window.simulation_run_mode_combo.isVisible() is True
        assert window.simulation_run_mode_combo.parentWidget() is window.workspace_toolbar


def test_top10_subbar_hidden_on_input_side_even_when_modus_lcc() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QMessageBox

    from rcm_desktop.adapter.workspace_view_registry import SIDE_INPUT
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
    from tests.test_desktop_results_workspace_window import _ensure_app

    app = _ensure_app()
    from unittest.mock import patch

    with patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok):
        window = ResultsWorkspaceWindow()
        window.show()
        window.workspace_state.set_active_view("output.lcc_plot")
        window.workspace_state.set_workspace_side(SIDE_INPUT)
        app.processEvents()
        assert window.workspace_state.snapshot().workspace_side == SIDE_INPUT
        assert window.workspace_state.snapshot().modus == MODE_LCC
        assert window.top10_subbar.isVisible() is False
