from __future__ import annotations

import json
from pathlib import Path

from rcm_core.cache import compute_fm_hash, compute_global_digest, save_cache
from rcm_core.models import FMResult, RCMProject
from rcm_core.persistence import load_project

from rcm_desktop.adapter.analysis_cache_service import (
    fm_cache_available,
    hydrate_run_from_cache,
)


def _fm(fm_id: str) -> FMResult:
    return FMResult(
        fm_id=fm_id,
        pbs_id="PBS-1",
        p_failure_lifecycle=0.1,
        expected_failures=1.0,
        expected_raw_downtime_hr=1.0,
        expected_detection_delay_hr=0.0,
        expected_total_downtime_hr=1.0,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=10.0,
        pm_cost_eur=5.0,
        total_cost_eur=15.0,
        risk_contribution=0.01,
    )


def test_hydrate_run_from_cache_returns_done_run_when_digest_matches(tmp_path):
    from rcm_desktop.adapter.run_service import run as run_single

    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    project_path = tmp_path / "demo.rcm.json"
    project_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

    initial = run_single(project, project_path)
    assert initial.status == "done"

    assert fm_cache_available(project, project_path) is True
    hydrated = hydrate_run_from_cache(project, project_path)
    assert hydrated is not None
    assert hydrated.status == "done"
    assert hydrated.metrics.fm_result_count == initial.metrics.fm_result_count


def test_hydrate_returns_none_when_project_digest_mismatch(tmp_path):
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    project_path = tmp_path / "demo.rcm.json"
    project_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

    fm = _fm("FM-1")
    hashes = {fm.fm_id: compute_fm_hash(project, fm.fm_id)}
    save_cache(project_path, hashes, {fm.fm_id: fm}, project)

    mutated = RCMProject.from_dict(project.to_dict())
    mutated.config.lifecycle_years = float(project.config.lifecycle_years) + 1.0

    assert hydrate_run_from_cache(mutated, project_path) is None
    assert fm_cache_available(mutated, project_path) is False


def test_hydrate_returns_none_when_fm_hash_stale(tmp_path):
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    project_path = tmp_path / "demo.rcm.json"
    project_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

    fm = _fm("FM-1")
    save_cache(project_path, {"FM-1": "stale-hash"}, {fm.fm_id: fm}, project)

    assert hydrate_run_from_cache(project, project_path) is None
