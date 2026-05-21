"""Slice 36 performance contracts — call-count + cache-hit (geen flaky timing in CI).

Run: pytest -m perf tests/perf/test_slice36_regression.py
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from rcm_core.incremental_run import run_incremental_analysis
from rcm_core.persistence import load_project
from rcm_desktop.adapter import lcc_planning_service
from rcm_desktop.adapter.lcc_planning_service import build_lcc_year_detail
from rcm_desktop.adapter.ltap_view_cache import invalidate_ltap_view_cache
from rcm_desktop.adapter.results_workspace_state import MODE_BIJDRAGEN, ResultsWorkspaceState
from rcm_desktop.adapter.run_service import run as run_single
from rcm_desktop.adapter.workspace_detail_render_scope import required_detail_builders

PERF_DIR = Path(__file__).parent
BASELINE_PATH = PERF_DIR / "baseline.json"
ONE_FM_FIXTURE = Path("tests/fixtures/one_fm_planning.rcm.json")


@pytest.fixture(scope="module")
def baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def contracts(baseline: dict) -> dict:
    section = baseline.get("slice36_contracts")
    assert section is not None, "baseline.json missing slice36_contracts"
    return section


@pytest.mark.perf
def test_incremental_rerun_recalculates_zero_fms(tmp_path: Path, contracts: dict) -> None:
    """Tweede run op ongewijzigd project = cache-only (issue 01)."""
    project = load_project(ONE_FM_FIXTURE)
    project_path = tmp_path / "one_fm_planning.rcm.json"
    shutil.copy(ONE_FM_FIXTURE, project_path)

    first = run_incremental_analysis(
        project,
        project_path,
        full_recompute=True,
        parallel=False,
    )
    assert first.recalculated_fm_count > 0

    second = run_incremental_analysis(
        project,
        project_path,
        full_recompute=False,
        parallel=True,
    )
    assert second.cache_only is True
    assert second.recalculated_fm_count <= contracts["cache_hit_recalculated_fm_count_max"]


@pytest.mark.perf
def test_run_service_start_path_uses_incremental_on_repeat(tmp_path: Path, contracts: dict) -> None:
    """Adapter-run via run_service met full_recompute=False na warm cache."""
    project = load_project(ONE_FM_FIXTURE)
    project_path = tmp_path / "one_fm_planning.rcm.json"
    shutil.copy(ONE_FM_FIXTURE, project_path)

    warm = run_single(project, project_path, full_recompute=True, parallel=False)
    assert warm.status == "done"

    captured: dict[str, object] = {}
    import rcm_desktop.adapter.run_service as run_service_mod

    original = run_service_mod.run_incremental_analysis

    def spy(project_arg, path_arg, **kwargs):
        captured["kwargs"] = kwargs
        return original(project_arg, path_arg, **kwargs)

    run_service_mod.run_incremental_analysis = spy
    try:
        repeat = run_single(project, project_path, full_recompute=False, parallel=True)
    finally:
        run_service_mod.run_incremental_analysis = original

    assert repeat.status == "done"
    assert captured["kwargs"] == {
        "full_recompute": False,
        "parallel": True,
        "scenario_key": None,
    }


@pytest.mark.perf
def test_lcc_planning_curve_respects_ltap_call_budget(
    monkeypatch: pytest.MonkeyPatch,
    contracts: dict,
) -> None:
    project = load_project(ONE_FM_FIXTURE)
    rr = run_single(project, ONE_FM_FIXTURE, full_recompute=True, parallel=False)
    assert rr.status == "done"

    invalidate_ltap_view_cache()
    calls = {"n": 0}
    original = lcc_planning_service.get_ltap_view

    def counting(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(lcc_planning_service, "get_ltap_view", counting)
    lcc_planning_service.build_lcc_planning_curve_reconciled(project, rr)
    assert calls["n"] <= contracts["lcc_curve_ltap_calls_max"]


@pytest.mark.perf
def test_lcc_chart_plus_year_detail_reuses_ltap_cache(
    monkeypatch: pytest.MonkeyPatch,
    contracts: dict,
) -> None:
    """Simuleert werkruimte-LCC-tick: curve + jaardetail (issue 02 + 03)."""
    project = load_project(ONE_FM_FIXTURE)
    rr = run_single(project, ONE_FM_FIXTURE, full_recompute=True, parallel=False)
    assert rr.status == "done"

    invalidate_ltap_view_cache()
    from rcm_desktop.adapter import ltap_service

    builds = {"n": 0}
    original_build = ltap_service.build_ltap_view

    def counting_build(*args, **kwargs):
        builds["n"] += 1
        return original_build(*args, **kwargs)

    monkeypatch.setattr(ltap_service, "build_ltap_view", counting_build)

    curve = lcc_planning_service.build_lcc_planning_curve_reconciled(project, rr)
    assert curve is not None
    calendar_year = int(project.config.modeljaar)

    curve_rebuilds = {"n": 0}
    original_curve = lcc_planning_service.build_lcc_planning_curve_reconciled

    def counting_curve(*args, **kwargs):
        curve_rebuilds["n"] += 1
        return original_curve(*args, **kwargs)

    monkeypatch.setattr(
        lcc_planning_service,
        "build_lcc_planning_curve_reconciled",
        counting_curve,
    )
    build_lcc_year_detail(
        project,
        rr,
        calendar_year,
        planning_curve=curve,
    )

    assert curve_rebuilds["n"] <= contracts["lcc_year_detail_curve_rebuilds_with_injected_curve_max"]
    assert builds["n"] <= contracts["lcc_render_cycle_ltap_builds_max"]


@pytest.mark.perf
def test_metric_toggle_in_bijdragen_does_not_require_lcc(contracts: dict) -> None:
    snap = ResultsWorkspaceState().snapshot()
    snap = snap.__class__(
        **{
            **{f.name: getattr(snap, f.name) for f in snap.__dataclass_fields__.values()},
            "modus": MODE_BIJDRAGEN,
            "metric": "kosten",
        }
    )
    required = required_detail_builders(snap, "active_modus_only")
    assert "lcc" not in required
    assert required == frozenset({MODE_BIJDRAGEN})


@pytest.mark.perf
def test_baseline_documents_haarlem_timing_reference(baseline: dict) -> None:
    """Handmatige referentie uit pre-slice-24 (niet als CI-timing assertie)."""
    assert baseline["fixture"].endswith("awzi_haarlem_waarderpolder_demo.rcm.json")
    assert baseline["cm_repeat_run_seconds"] == 5.0
    assert Path(baseline["fixture"]).is_file()
