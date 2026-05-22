"""Slice 38 issue 02 — curve-builder dedup."""
from __future__ import annotations

import json
from pathlib import Path

from rcm_core.models import RCMProject
from rcm_desktop.adapter import lcc_planning_service
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.run_service import run as run_single


def _fixture_run():
    fixture = Path("tests/fixtures/one_fm_planning.rcm.json")
    project = RCMProject.from_dict(json.loads(fixture.read_text(encoding="utf-8")))
    rr = run_single(project, fixture, full_recompute=True, parallel=False)
    assert rr.status == "done"
    return project, rr


def test_inactive_overlay_calls_ltap_at_most_once(monkeypatch):
    project, rr = _fixture_run()
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
    assert calls["n"] <= 1


def test_reconcile_called_at_most_once_per_curve_build(monkeypatch):
    project, rr = _fixture_run()
    calls = {"n": 0}
    original = lcc_planning_service.reconcile_planning_curve_pm_total

    def counting(curve, target_pm):
        calls["n"] += 1
        return original(curve, target_pm)

    monkeypatch.setattr(lcc_planning_service, "reconcile_planning_curve_pm_total", counting)
    lcc_planning_service.build_lcc_planning_curve_reconciled(project, rr)
    assert calls["n"] <= 1
