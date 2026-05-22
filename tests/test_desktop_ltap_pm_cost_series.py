"""Slice 38 issue 03 — LTAP PM cost series light path."""
from __future__ import annotations

import json
from pathlib import Path

from rcm_core.models import RCMProject
from rcm_desktop.adapter import lcc_planning_service
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.ltap_pm_cost_series import build_ltap_pm_cost_series
from rcm_desktop.adapter.ltap_service import build_ltap_view
from rcm_desktop.adapter.ltap_view_cache import invalidate_ltap_view_cache
from rcm_desktop.adapter.run_service import run as run_single


def _fixture_run():
    fixture = Path("tests/fixtures/one_fm_planning.rcm.json")
    project = RCMProject.from_dict(json.loads(fixture.read_text(encoding="utf-8")))
    rr = run_single(project, fixture, full_recompute=True, parallel=False)
    assert rr.status == "done"
    return project, rr


def test_light_path_pm_totals_match_full_ltap_view():
    project, _rr = _fixture_run()
    filters = LCCTypeFilterSet.all_on()
    raw, filtered = build_ltap_pm_cost_series(
        project,
        type_filters=filters,
    )
    view = build_ltap_view(project)
    for row in view.years:
        assert raw[row.year] == row.pm_cost_eur
        expected_filtered = 0.0
        seen: set[str] = set()
        for detail in row.details:
            if detail.pm_id in seen:
                continue
            task = project.pm_tasks.get(detail.pm_id)
            if task is None or not filters.task_matches(task):
                continue
            seen.add(detail.pm_id)
            expected_filtered += detail.pm_cost_eur
        assert filtered[row.year] == expected_filtered


def test_curve_build_uses_light_path_not_full_ltap_view(monkeypatch):
    project, rr = _fixture_run()
    invalidate_ltap_view_cache()
    calls = {"view": 0, "light": 0}
    original_view = lcc_planning_service.get_ltap_view
    original_light = lcc_planning_service.build_ltap_pm_cost_series

    def counting_view(*args, **kwargs):
        calls["view"] += 1
        return original_view(*args, **kwargs)

    def counting_light(*args, **kwargs):
        calls["light"] += 1
        return original_light(*args, **kwargs)

    monkeypatch.setattr(lcc_planning_service, "get_ltap_view", counting_view)
    monkeypatch.setattr(lcc_planning_service, "build_ltap_pm_cost_series", counting_light)
    lcc_planning_service.build_lcc_planning_curve_reconciled(project, rr)
    assert calls["light"] >= 1
    assert calls["view"] == 0
