"""Slice 38 issue 05 — LCC achtergrond-warmup."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from rcm_core.models import RCMProject
from rcm_desktop.adapter.lcc_render_cache_service import build_lcc_curve_cache_key
from rcm_desktop.adapter.lcc_warmup_runner import LCCWarmupRunner
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.presentation_lazy_service import warm_lcc_render_index
from rcm_desktop.adapter.results_workspace_state import METRIC_NIET_BESCHIKBAARHEID, MODE_LCC, WorkspaceStateSnapshot
from rcm_desktop.adapter.run_service import run as run_single
from rcm_desktop.adapter.workspace_render_index import SLOT_CURRENT, WorkspaceRenderIndex


@pytest.fixture(scope="module")
def qt_app():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


def _fixture_run():
    fixture = Path("tests/fixtures/one_fm_planning.rcm.json")
    project = RCMProject.from_dict(json.loads(fixture.read_text(encoding="utf-8")))
    rr = run_single(project, fixture, full_recompute=True, parallel=False)
    assert rr.status == "done"
    return project, rr


def test_warmup_populates_render_index(qt_app):
    project, rr = _fixture_run()
    render_index = WorkspaceRenderIndex()
    runner = LCCWarmupRunner()
    snapshot = WorkspaceStateSnapshot(
        modus=MODE_LCC,
        source="pbs",
        metric=METRIC_NIET_BESCHIKBAARHEID,
        top_n=10,
        scope_id=None,
        filter_text="",
        lcc_filters=LCCTypeFilterSet.all_on(),
        lcc_calendar_year=None,
        planning_overlay=PlanningOverlayState.inactive(),
    )
    key = build_lcc_curve_cache_key(snapshot)
    assert runner.start(project, rr, render_index, snapshot) is True
    while runner.busy:
        qt_app.processEvents()
    curve = render_index.get_or_build(
        SLOT_CURRENT,
        None,
        key,
        lambda: (_ for _ in ()).throw(AssertionError("should be cached")),
    )
    assert curve is not None
    assert curve.display_buckets


def test_warmup_skips_when_busy(qt_app):
    project, rr = _fixture_run()
    render_index = WorkspaceRenderIndex()
    runner = LCCWarmupRunner()
    snapshot = WorkspaceStateSnapshot(
        modus=MODE_LCC,
        source="pbs",
        metric="nb",
        top_n=10,
        scope_id=None,
        filter_text="",
    )
    assert runner.start(project, rr, render_index, snapshot) is True
    assert runner.start(project, rr, render_index, snapshot) is False
    while runner.busy:
        qt_app.processEvents()
