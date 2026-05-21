"""Slice 36 issue 02 — LTAP presentatie-cache tests."""
from __future__ import annotations

import json
from pathlib import Path

from rcm_core.models import RCMProject
from rcm_desktop.adapter import lcc_planning_service
from rcm_desktop.adapter.ltap_view_cache import LTAPViewCache, get_ltap_view, invalidate_ltap_view_cache
from rcm_desktop.adapter.run_service import run as run_single


def _sample_project() -> RCMProject:
    raw = json.loads(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def test_ltap_cache_returns_same_view_for_identical_kwargs():
    cache = LTAPViewCache()
    project = _sample_project()
    first = cache.get(project)
    second = cache.get(project)
    assert first is second


def test_ltap_cache_misses_when_overlay_anchor_changes():
    cache = LTAPViewCache()
    project = _sample_project()
    pm_id = next(iter(project.pm_tasks))
    baseline = cache.get(project)
    shifted = cache.get(project, overlay_anchor_years={pm_id: 1.0})
    assert baseline is not shifted


def test_ltap_cache_clears_on_project_change():
    cache = LTAPViewCache()
    project_a = _sample_project()
    first = cache.get(project_a)
    cache.clear_for_project_change()
    second = cache.get(project_a)
    assert first is not second


def test_module_get_ltap_view_uses_shared_cache():
    invalidate_ltap_view_cache()
    project = _sample_project()
    first = get_ltap_view(project)
    second = get_ltap_view(project)
    assert first is second


def test_lcc_planning_curve_calls_ltap_at_most_once_for_inactive_overlay(monkeypatch):
    """Inactive overlay: één light-path LTAP-build per curve (slice 38)."""
    fixture = Path("tests/fixtures/one_fm_planning.rcm.json")
    project = RCMProject.from_dict(json.loads(fixture.read_text(encoding="utf-8")))
    rr = run_single(project, fixture, full_recompute=True, parallel=False)
    assert rr.status == "done"

    invalidate_ltap_view_cache()
    calls = {"n": 0}
    original = lcc_planning_service.build_ltap_pm_cost_series

    def counting_build(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(lcc_planning_service, "build_ltap_pm_cost_series", counting_build)

    lcc_planning_service.build_lcc_planning_curve_reconciled(project, rr)
    assert calls["n"] == 1
