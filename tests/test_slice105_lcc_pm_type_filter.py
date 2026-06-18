"""Slice 105 HILT105 B5 — LCC PM-type filter wijzigt Tijdsplot-curve."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_core.models import RCMProject

from rcm_desktop.adapter.lcc_planning_service import build_lcc_planning_curve_reconciled
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.results_workspace_state import METRIC_KOSTEN
from rcm_desktop.adapter.run_service import run as run_single
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import _ensure_app

HAARLEM = Path("tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json")


def _rev_only_filters() -> LCCTypeFilterSet:
    return LCCTypeFilterSet(
        cm=True, rev=True, in_task=False, tst=False, svo=False, wet=False
    )


def _in_only_filters() -> LCCTypeFilterSet:
    return LCCTypeFilterSet(
        cm=True, rev=False, in_task=True, tst=False, svo=False, wet=False
    )


def _open_haarlem_lcc_kosten(window: ResultsWorkspaceWindow, monkeypatch) -> None:
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    project = RCMProject.from_dict(json.loads(HAARLEM.read_text(encoding="utf-8")))
    window._state.set_last_project(project)
    rr = run_single(project, HAARLEM, full_recompute=True, parallel=False)
    assert rr.status == "done"
    window._state.set_last_run(rr)
    window.show()
    window.workspace_state.set_active_view("output.lcc_plot")
    window.workspace_state.set_metric(METRIC_KOSTEN)


def _chart_preventief_sum(window: ResultsWorkspaceWindow) -> float:
    return sum(b.preventief_eur for b in window.lcc_chart_widget.buckets())


def test_lcc_pm_type_filter_rev_differs_from_in_on_haarlem_adapter() -> None:
    project = RCMProject.from_dict(json.loads(HAARLEM.read_text(encoding="utf-8")))
    rr = run_single(project, HAARLEM, full_recompute=True, parallel=False)
    assert rr.status == "done"

    rev_curve = build_lcc_planning_curve_reconciled(
        project, rr, type_filters=_rev_only_filters()
    )
    in_curve = build_lcc_planning_curve_reconciled(
        project, rr, type_filters=_in_only_filters()
    )
    assert rev_curve is not None and in_curve is not None

    rev_sum = sum(b.preventief_eur for b in rev_curve.display_buckets)
    in_sum = sum(b.preventief_eur for b in in_curve.display_buckets)
    all_sum = sum(
        b.preventief_eur
        for b in build_lcc_planning_curve_reconciled(
            project, rr, type_filters=LCCTypeFilterSet.all_on()
        ).display_buckets
    )

    assert rev_sum > 0.0
    assert in_sum > 0.0
    assert not math.isclose(rev_sum, in_sum, rel_tol=0, abs_tol=1.0)
    assert math.isclose(rev_sum + in_sum, all_sum, rel_tol=0, abs_tol=1.0)


def test_lcc_pm_type_filter_updates_chart_widget(monkeypatch) -> None:
    app = _ensure_app()
    window = ResultsWorkspaceWindow()
    _open_haarlem_lcc_kosten(window, monkeypatch)
    app.processEvents()

    for key in ("rev", "in_task", "tst", "svo", "wet"):
        window._lcc_filter_checks[key].setChecked(key == "rev")
    window._on_lcc_filter_toggled()
    app.processEvents()
    rev_sum = _chart_preventief_sum(window)

    for key in ("rev", "in_task", "tst", "svo", "wet"):
        window._lcc_filter_checks[key].setChecked(key == "in_task")
    window._on_lcc_filter_toggled()
    app.processEvents()
    in_sum = _chart_preventief_sum(window)

    assert rev_sum > 0.0
    assert in_sum > 0.0
    assert not math.isclose(rev_sum, in_sum, rel_tol=0, abs_tol=1.0)
