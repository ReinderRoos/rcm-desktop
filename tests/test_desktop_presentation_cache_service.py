from __future__ import annotations

import json
from pathlib import Path

from rcm_core.cache import compute_fm_hash, save_cache
from rcm_core.models import FMResult
from rcm_core.persistence import load_project

from rcm_desktop.adapter.presentation_cache_service import (
    PRESENTATION_CACHE_VERSION,
    PresentationProjectTotal,
    attach_presentation_to_cache,
    build_project_total_presentation,
    load_presentation_from_cache,
    presentation_dict_to_dto,
    presentation_dto_to_dict,
    presentation_needs_rebuild,
)


def _fm(fm_id: str) -> FMResult:
    return FMResult(
        fm_id=fm_id,
        pbs_id="PBS-1",
        p_failure_lifecycle=0.1,
        expected_failures=2.0,
        expected_raw_downtime_hr=2.0,
        expected_detection_delay_hr=0.0,
        expected_total_downtime_hr=2.0,
        expected_pm_downtime_hr=0.5,
        expected_cm_cost_eur=20.0,
        pm_cost_eur=10.0,
        total_cost_eur=30.0,
        risk_contribution=0.02,
    )


def test_presentation_roundtrip_dict_preserves_lcc_bucket_count():
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    from rcm_desktop.adapter.run_service import run

    run_result = run(project, fixture)
    assert run_result.status == "done"

    dto = build_project_total_presentation(project, run_result)
    assert len(dto.lcc_buckets) > 0
    assert len(dto.unavailability_rows) > 0
    assert len(dto.pm_kosten_rows) > 0
    assert len(dto.pm_aantal_rows) > 0
    assert len(dto.contribution_rows) > 0

    payload = presentation_dto_to_dict(dto)
    restored = presentation_dict_to_dto(payload)
    assert len(restored.lcc_buckets) == len(dto.lcc_buckets)
    assert restored.lcc_buckets[0].calendar_year == dto.lcc_buckets[0].calendar_year


def test_attach_and_load_presentation_from_cache_file(tmp_path):
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    project_path = tmp_path / "demo.rcm.json"
    project_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

    fm = _fm("FM-1")
    hashes = {fm.fm_id: compute_fm_hash(project, fm.fm_id)}
    save_cache(project_path, hashes, {fm.fm_id: fm}, project)

    from rcm_desktop.adapter.run_service import run

    run_result = run(project, project_path)
    dto = build_project_total_presentation(project, run_result)
    attach_presentation_to_cache(project_path, project, dto)

    loaded = load_presentation_from_cache(project, project_path)
    assert loaded is not None
    assert len(loaded.lcc_buckets) == len(dto.lcc_buckets)


def test_presentation_needs_rebuild_when_version_mismatch():
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    project_path = Path("tests/fixtures/sample_project.rcm.json")
    cache_path = project_path.with_suffix("").with_suffix(".rcm.cache.json")
    if not cache_path.exists():
        return

    raw = json.loads(cache_path.read_text(encoding="utf-8"))
    raw["presentation"] = {
        "presentation_cache_version": PRESENTATION_CACHE_VERSION + 99,
        "built_at_digest": raw.get("global_digest", ""),
        "project_total": {},
    }
    cache_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    assert presentation_needs_rebuild(project, project_path) is True
