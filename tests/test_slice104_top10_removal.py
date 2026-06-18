"""Slice 104 issue 04 — Top 10 modus verwijderd."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.results_workspace_state import (
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    ResultsWorkspaceState,
    normalize_modus,
)
from rcm_desktop.adapter.workspace_view_menu import workspace_view_menu_groups
from rcm_desktop.adapter.workspace_view_registry import (
    DEFAULT_VIEW_BY_SIDE,
    SIDE_OUTPUT,
    WORKSPACE_VIEW_REGISTRY,
    enabled_views_for_side,
    migrate_workspace_view_id,
    view_by_id,
)
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app


def test_normalize_modus_maps_bijdragen_to_fm_detail() -> None:
    assert normalize_modus(MODE_BIJDRAGEN) == MODE_FM_DETAIL


def test_default_output_view_is_fm_results() -> None:
    assert DEFAULT_VIEW_BY_SIDE[SIDE_OUTPUT] == "output.fm_results"


def test_top_10_view_disabled_in_registry() -> None:
    entry = view_by_id(WORKSPACE_VIEW_REGISTRY, "output.top_10")
    assert entry is not None
    assert entry.enabled is False


def test_migrate_workspace_view_id_maps_top_10() -> None:
    assert migrate_workspace_view_id("output.top_10") == "output.fm_results"
    assert migrate_workspace_view_id("output.lcc_plot") == "output.lcc_plot"


def test_workspace_state_default_modus_is_fm_detail() -> None:
    state = ResultsWorkspaceState()
    assert state.snapshot().modus == MODE_FM_DETAIL
    assert state.snapshot().active_view_id == "output.fm_results"


def test_restore_navigation_migrates_retired_top_10_view() -> None:
    state = ResultsWorkspaceState()
    state.restore_navigation(SIDE_OUTPUT, {SIDE_OUTPUT: "output.top_10"})
    assert state.snapshot().active_view_id == "output.fm_results"
    assert state.snapshot().modus == MODE_FM_DETAIL


def test_top_10_excluded_from_navigation_dropdown() -> None:
    view_ids = [entry.view_id for entry in enabled_views_for_side(WORKSPACE_VIEW_REGISTRY, SIDE_OUTPUT)]
    assert "output.top_10" not in view_ids


def test_top_10_excluded_from_beeld_menu() -> None:
    view_ids = {
        item.view_id
        for group in workspace_view_menu_groups()
        for item in group.items
        if item.view_id is not None
    }
    assert "output.top_10" not in view_ids


def test_new_window_opens_on_fm_detail(monkeypatch, isolated_navigation_settings) -> None:
    _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    assert window.workspace_state.snapshot().modus == MODE_FM_DETAIL
    assert window.detail_stack.currentWidget() is window.fm_detail_page
