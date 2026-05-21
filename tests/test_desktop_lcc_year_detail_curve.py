"""Slice 36 issue 03 — LCC jaardetail hergebruikt planningcurve."""
from __future__ import annotations

import json
from pathlib import Path

from rcm_core.models import RCMProject
from rcm_desktop.adapter import lcc_planning_service
from rcm_desktop.adapter.lcc_planning_service import (
    LCCPlanningCurve,
    LCCYearBucket,
    build_lcc_year_detail,
)
from rcm_desktop.adapter.run_service import run as run_single


def _fixture_run():
    fixture = Path("tests/fixtures/one_fm_planning.rcm.json")
    project = RCMProject.from_dict(json.loads(fixture.read_text(encoding="utf-8")))
    rr = run_single(project, fixture, full_recompute=True, parallel=False)
    assert rr.status == "done"
    return project, rr


def test_year_detail_with_injected_curve_skips_curve_rebuild(monkeypatch):
    project, rr = _fixture_run()
    curve = lcc_planning_service.build_lcc_planning_curve_reconciled(project, rr)
    assert curve is not None

    def fail_rebuild(*_args, **_kwargs):
        raise AssertionError("curve rebuild should not run when curve is injected")

    monkeypatch.setattr(
        lcc_planning_service,
        "build_lcc_planning_curve_reconciled",
        fail_rebuild,
    )

    calendar_year = int(project.config.modeljaar)
    detail = build_lcc_year_detail(
        project,
        rr,
        calendar_year,
        planning_curve=curve,
    )
    assert detail is not None


def test_year_detail_without_curve_still_builds(monkeypatch):
    project, rr = _fixture_run()
    calls = {"n": 0}
    original = lcc_planning_service.build_lcc_planning_curve_reconciled

    def counting(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(
        lcc_planning_service,
        "build_lcc_planning_curve_reconciled",
        counting,
    )

    calendar_year = int(project.config.modeljaar)
    build_lcc_year_detail(project, rr, calendar_year)
    assert calls["n"] == 1
