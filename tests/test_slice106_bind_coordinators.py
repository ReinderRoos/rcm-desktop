"""Slice 106 issue 03 — bind coordinators + venster cleanup."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.faalwijze_analyse_service import FM_COMPARE_VIEW_DIAGRAM
from rcm_desktop.adapter.result_view_service import FMResultRow
from rcm_desktop.adapter.results_workspace_orchestrator import RenderPlan
from rcm_desktop.adapter.workspace_view_service import FMDetailView
from rcm_desktop.views.panels.fm_detail_bind_coordinator import FmDetailBindCoordinator
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app

WORKSPACE_WINDOW = (
    Path(__file__).resolve().parent.parent
    / "rcm_desktop"
    / "views"
    / "results_workspace_window.py"
)

FORBIDDEN_FM_PASSTHROUGH_PATTERNS = (
    "def _sync_fm_",
    "def _set_fm_",
    "def _apply_fm_compare_panels",
    "def _apply_fm_single_presentation",
    "def _layout_fm_compare_chart",
    "def _layout_fm_single_chart",
)


def test_workspace_window_has_no_fm_passthrough_forwards() -> None:
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_FM_PASSTHROUGH_PATTERNS:
        assert pattern not in source, f"unexpected FM passthrough {pattern!r}"


def test_window_exposes_fm_detail_bind_coordinator() -> None:
    _ensure_app()
    window = ResultsWorkspaceWindow()
    assert isinstance(window._fm_bind, FmDetailBindCoordinator)


def test_coordinator_set_view_mode_updates_snapshot(monkeypatch) -> None:
    _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window._fm_bind.set_view_mode(FM_COMPARE_VIEW_DIAGRAM)
    assert window._fm_bind.view_mode == FM_COMPARE_VIEW_DIAGRAM


def test_coordinator_apply_render_delegates_fm(monkeypatch) -> None:
    _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    calls: list[str] = []

    def _capture_fm(window, plan, snapshot):
        calls.append("fm")

    monkeypatch.setattr(
        "rcm_desktop.views.panels.fm_detail_workspace_binding.apply_fm_detail_render",
        _capture_fm,
    )
    window = ResultsWorkspaceWindow()
    snap = window.workspace_state.snapshot()
    plan = RenderPlan(
        kind="fm",
        fm=FMDetailView(
            fm_rows=(
                FMResultRow(
                    fm_id="FM-A",
                    faalwijze_omschrijving="A",
                    pbs_id="PBS-1",
                    bouwdeel_naam="BD",
                    expected_failures=1.0,
                    expected_total_downtime_hr=1.0,
                    total_cost_eur=1.0,
                ),
            ),
        ),
    )
    window._fm_bind.apply_render(plan, snap)
    assert calls == ["fm"]


def test_apply_render_plan_uses_coordinator(monkeypatch) -> None:
    _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    calls: list[str] = []

    def _capture(window, plan, snapshot):
        calls.append(plan.kind)

    monkeypatch.setattr(
        FmDetailBindCoordinator,
        "apply_render",
        lambda self, plan, snapshot: _capture(self._window, plan, snapshot),
    )
    window = ResultsWorkspaceWindow()
    snap = window.workspace_state.snapshot()
    fm_plan = RenderPlan(
        kind="fm",
        fm=FMDetailView(fm_rows=()),
    )
    window._apply_render_plan(fm_plan, snap)
    assert calls == ["fm"]
