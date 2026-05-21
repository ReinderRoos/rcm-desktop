"""Tests voor incremental_run — gedeelde incrementele/volledige run-orchestratie."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from concurrent.futures.process import BrokenProcessPool

import rcm_core.incremental_run as ir
from rcm_core.cache import CacheSnapshot
from rcm_core.incremental_run import IncrementalRunResult, run_incremental_analysis
from rcm_core.models import FMResult
from rcm_core.persistence import load_project


@pytest.fixture
def sample_project():
    fixture = Path(__file__).parent / "fixtures" / "sample_project.rcm.json"
    return load_project(fixture)


def _minimal_fm_result(fm_id: str, pbs_id: str) -> dict:
    return FMResult(
        fm_id=fm_id,
        pbs_id=pbs_id,
        p_failure_lifecycle=0.5,
        expected_failures=1.0,
        expected_raw_downtime_hr=0.0,
        expected_detection_delay_hr=0.0,
        expected_total_downtime_hr=0.0,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=10.0,
        pm_cost_eur=5.0,
        total_cost_eur=15.0,
        risk_contribution=0.2,
    ).to_dict()


def test_cache_only_does_not_call_save_cache(sample_project, monkeypatch):
    """Bij actuele cache geen save_cache; wel FM/PBS-resultaten."""
    fm_id = next(iter(sample_project.faalwijzes.keys()))
    fm = sample_project.faalwijzes[fm_id]
    cached_raw = {fm_id: _minimal_fm_result(fm_id, fm.pbs_id)}
    monkeypatch.setattr(
        ir,
        "load_cache_snapshot",
        lambda _proj, _path, **_kw: CacheSnapshot({}, cached_raw, True, True),
    )
    monkeypatch.setattr(ir, "find_affected_fms", lambda _project, _h: [])

    saves: list[bool] = []

    def _no_save(*_a, **_k):
        saves.append(True)

    monkeypatch.setattr(ir, "save_cache", _no_save)

    result = run_incremental_analysis(
        sample_project,
        Path(__file__).parent / "fixtures" / "sample_project.rcm.json",
        full_recompute=False,
        parallel=False,
    )

    assert isinstance(result, IncrementalRunResult)
    assert result.cache_only is True
    assert result.recalculated_fm_count == 0
    assert saves == []
    assert fm_id in result.fm_results


def test_broken_process_pool_retries_sequential(sample_project, monkeypatch):
    calls: list[bool] = []

    def fake_run_analytical(project, fm_ids=None, parallel=True):
        calls.append(parallel)
        if parallel:
            raise BrokenProcessPool("pool broken")
        return ({}, {})

    monkeypatch.setattr(ir, "run_analytical", fake_run_analytical)
    monkeypatch.setattr(ir, "save_cache", lambda *_a, **_k: None)
    monkeypatch.setattr(ir, "_build_fm_hashes", lambda _p: {})

    result = run_incremental_analysis(
        sample_project,
        Path(__file__).parent / "fixtures" / "sample_project.rcm.json",
        full_recompute=True,
        parallel=True,
    )

    assert calls == [True, False]
    assert result.parallel_retried_sequential is True
    assert isinstance(result.pbs_results, dict)
