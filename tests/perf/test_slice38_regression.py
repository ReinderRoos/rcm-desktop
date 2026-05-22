"""Slice 38 performance contracts — LCC snel zichtbaar.

Run: pytest -m perf tests/perf/test_slice38_regression.py
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from rcm_core.persistence import load_project
from rcm_desktop.adapter import lcc_planning_service
from rcm_desktop.adapter.lcc_planning_service import build_lcc_year_detail
from rcm_desktop.adapter.lcc_render_cache_service import build_lcc_curve_cache_key
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.lcc_warmup_runner import LCCWarmupRunner
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.presentation_lazy_service import default_lcc_warmup_snapshot
from rcm_desktop.adapter.results_workspace_state import MODE_LCC, WorkspaceStateSnapshot
from rcm_desktop.adapter.run_service import run as run_single
from rcm_desktop.adapter.workspace_render_index import SLOT_CURRENT, WorkspaceRenderIndex

PERF_DIR = Path(__file__).parent
BASELINE_PATH = PERF_DIR / "baseline.json"
ONE_FM_FIXTURE = Path("tests/fixtures/one_fm_planning.rcm.json")


@pytest.fixture(scope="module")
def baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def contracts(baseline: dict) -> dict:
    section = baseline.get("slice38_contracts")
    assert section is not None, "baseline.json missing slice38_contracts"
    return section


@pytest.fixture(scope="module")
def qt_app():
    from PySide6.QtCore import QCoreApplication

    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


def _lcc_snapshot(**kwargs) -> WorkspaceStateSnapshot:
    base = WorkspaceStateSnapshot(
        modus=MODE_LCC,
        source="pbs",
        metric="nb",
        top_n=10,
        scope_id=None,
        filter_text="",
        lcc_filters=LCCTypeFilterSet.all_on(),
        lcc_calendar_year=None,
        planning_overlay=PlanningOverlayState.inactive(),
    )
    return replace(base, **kwargs)


@pytest.mark.perf
def test_year_click_does_not_change_curve_cache_key(contracts: dict) -> None:
    snap_a = _lcc_snapshot(lcc_calendar_year=None)
    snap_b = _lcc_snapshot(lcc_calendar_year=2030)
    assert build_lcc_curve_cache_key(snap_a) == build_lcc_curve_cache_key(snap_b)


@pytest.mark.perf
def test_inactive_overlay_light_path_call_budget(
    monkeypatch: pytest.MonkeyPatch,
    contracts: dict,
) -> None:
    project = load_project(ONE_FM_FIXTURE)
    rr = run_single(project, ONE_FM_FIXTURE, full_recompute=True, parallel=False)
    assert rr.status == "done"

    calls = {"n": 0}
    original = lcc_planning_service.build_ltap_pm_cost_series

    def counting(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(lcc_planning_service, "build_ltap_pm_cost_series", counting)
    lcc_planning_service.build_lcc_planning_curve_reconciled(
        project,
        rr,
        overlay=PlanningOverlayState.inactive(),
    )
    assert calls["n"] <= contracts["lcc_inactive_overlay_ltap_builds_max"]


@pytest.mark.perf
def test_reconcile_call_budget_per_curve(
    monkeypatch: pytest.MonkeyPatch,
    contracts: dict,
) -> None:
    project = load_project(ONE_FM_FIXTURE)
    rr = run_single(project, ONE_FM_FIXTURE, full_recompute=True, parallel=False)
    assert rr.status == "done"

    calls = {"n": 0}
    original = lcc_planning_service.reconcile_planning_curve_pm_total

    def counting(curve, target_pm):
        calls["n"] += 1
        return original(curve, target_pm)

    monkeypatch.setattr(lcc_planning_service, "reconcile_planning_curve_pm_total", counting)
    lcc_planning_service.build_lcc_planning_curve_reconciled(project, rr)
    assert calls["n"] <= contracts["lcc_reconcile_calls_per_curve_max"]


@pytest.mark.perf
def test_year_detail_with_injected_curve_no_rebuild(
    monkeypatch: pytest.MonkeyPatch,
    contracts: dict,
) -> None:
    project = load_project(ONE_FM_FIXTURE)
    rr = run_single(project, ONE_FM_FIXTURE, full_recompute=True, parallel=False)
    assert rr.status == "done"

    curve = lcc_planning_service.build_lcc_planning_curve_reconciled(project, rr)
    assert curve is not None

    rebuilds = {"n": 0}
    original = lcc_planning_service.build_lcc_planning_curve_reconciled

    def counting(*args, **kwargs):
        rebuilds["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(lcc_planning_service, "build_lcc_planning_curve_reconciled", counting)
    calendar_year = int(project.config.modeljaar)
    build_lcc_year_detail(project, rr, calendar_year, planning_curve=curve)
    build_lcc_year_detail(project, rr, calendar_year + 1, planning_curve=curve)
    assert rebuilds["n"] <= contracts["lcc_year_click_curve_rebuilds_max"]


@pytest.mark.perf
def test_post_run_warmup_builds_at_most_one_curve(
    monkeypatch: pytest.MonkeyPatch,
    contracts: dict,
    qt_app,
) -> None:
    from PySide6.QtCore import QCoreApplication

    app = QCoreApplication.instance() or qt_app
    project = load_project(ONE_FM_FIXTURE)
    rr = run_single(project, ONE_FM_FIXTURE, full_recompute=True, parallel=False)
    assert rr.status == "done"

    render_index = WorkspaceRenderIndex()
    snapshot = default_lcc_warmup_snapshot(_lcc_snapshot())
    builds = {"n": 0}
    original = lcc_planning_service.build_lcc_planning_curve_reconciled

    def counting(*args, **kwargs):
        builds["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(lcc_planning_service, "build_lcc_planning_curve_reconciled", counting)
    runner = LCCWarmupRunner()
    assert runner.start(project, rr, render_index, snapshot) is True
    while runner.busy:
        app.processEvents()
    assert builds["n"] <= contracts["post_run_lcc_warmup_builds_max"]
