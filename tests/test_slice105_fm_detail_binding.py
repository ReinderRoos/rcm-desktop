"""Slice 105 issue 11 — FM-detail workspace binding extractie."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.faalwijze_analyse_service import build_faalwijze_bundle_for_fm_view
from rcm_desktop.adapter.result_view_service import FMResultRow
from rcm_desktop.adapter.results_workspace_orchestrator import RenderPlan
from rcm_desktop.adapter.results_workspace_state import MODE_FM_DETAIL
from rcm_desktop.adapter.workspace_view_service import FMDetailView
from rcm_desktop.views.panels import fm_detail_workspace_binding as binding
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app, _inject_run, _three_level_project


def test_binding_exports_fm_render_entrypoints() -> None:
    assert callable(binding.apply_fm_detail_render)
    assert callable(binding.apply_fm_compare_render)
    assert callable(binding.render_fm_rows)


def test_window_apply_render_plan_delegates_fm_to_binding(monkeypatch) -> None:
    _ensure_app()
    calls: list[str] = []

    def _capture_fm(window, plan, snapshot):
        calls.append("fm")

    monkeypatch.setattr(
        "rcm_desktop.views.panels.fm_detail_workspace_binding.apply_fm_detail_render",
        _capture_fm,
    )
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    snap = window.workspace_state.snapshot()
    fm_plan = RenderPlan(
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
    window._apply_render_plan(fm_plan, snap)
    assert calls == ["fm"]


def test_binding_render_fm_rows_populates_table(monkeypatch) -> None:
    _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    window.workspace_state.set_modus(MODE_FM_DETAIL)
    rows = (
        FMResultRow(
            fm_id="FM-A",
            faalwijze_omschrijving="A",
            pbs_id="PBS-1",
            bouwdeel_naam="BD",
            expected_failures=42.0,
            expected_total_downtime_hr=1.0,
            total_cost_eur=100.0,
        ),
    )
    binding.render_fm_rows(
        window,
        rows,
        bundle=build_faalwijze_bundle_for_fm_view(
            FMDetailView(fm_rows=rows),
            metric=window.workspace_state.snapshot().metric,
        ),
    )
    assert window.fm_table_view.model() is not None
    assert window._fm_table_proxy.rowCount() == 1
