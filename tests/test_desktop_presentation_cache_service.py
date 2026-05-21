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
    build_contribution_presentation,
    build_project_total_presentation,
    load_presentation_from_cache,
    presentation_dict_to_dto,
    presentation_dto_to_dict,
    presentation_modus_needs_rebuild,
    presentation_needs_rebuild,
)
from rcm_desktop.adapter.results_workspace_state import MODE_BIJDRAGEN, MODE_LCC


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


def test_contribution_presentation_v3_roundtrip():
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    from rcm_desktop.adapter.run_service import run

    run_result = run(project, fixture)
    assert run_result.status == "done"

    dto = build_contribution_presentation(project, run_result)
    assert len(dto.contribution_rows) > 0
    assert dto.built_modi == frozenset({MODE_BIJDRAGEN})
    assert dto.lcc_buckets == ()
    assert dto.unavailability_rows == ()

    payload = presentation_dto_to_dict(dto)
    assert payload["presentation_cache_version"] == PRESENTATION_CACHE_VERSION
    assert payload["project_total"]["built_modi"] == [MODE_BIJDRAGEN]

    restored = presentation_dict_to_dto(payload)
    assert len(restored.contribution_rows) == len(dto.contribution_rows)
    assert restored.built_modi == frozenset({MODE_BIJDRAGEN})


def test_build_project_total_presentation_is_contribution_only():
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    from rcm_desktop.adapter.run_service import run

    run_result = run(project, fixture)
    dto = build_project_total_presentation(project, run_result)
    assert dto.built_modi == frozenset({MODE_BIJDRAGEN})
    assert dto.lcc_buckets == ()


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
    dto = build_contribution_presentation(project, run_result)
    attach_presentation_to_cache(project_path, project, dto)

    loaded = load_presentation_from_cache(project, project_path)
    assert loaded is not None
    assert len(loaded.contribution_rows) == len(dto.contribution_rows)
    assert loaded.built_modi == frozenset({MODE_BIJDRAGEN})


def test_v2_legacy_presentation_loads_with_inferred_built_modi():
    legacy_block = {
        "presentation_cache_version": 2,
        "built_at_digest": "",
        "project_total": {
            "lcc_buckets": [
                {
                    "calendar_year": 2026,
                    "correctief_eur": 1.0,
                    "preventief_eur": 2.0,
                }
            ],
            "unavailability_rows": [],
            "pm": {"kosten": [], "aantal_uitvoeringen": []},
            "contribution": {
                "source": "pbs",
                "metric": "niet_beschikbaarheid",
                "top_n": 10,
                "presentation": {
                    "horizon": "per_year",
                    "year_choice": "average",
                    "unavailability_display": "hours",
                },
                "rows": [
                    {
                        "category_id": "PBS-1",
                        "label": "x",
                        "value": 1.0,
                        "share_pct": 100.0,
                    }
                ],
            },
        },
    }
    dto = presentation_dict_to_dto(legacy_block)
    assert MODE_BIJDRAGEN in dto.built_modi
    assert MODE_LCC in dto.built_modi
    assert len(dto.lcc_buckets) == 1


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


def test_presentation_modus_needs_rebuild_lcc_always_false(tmp_path):
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    project_path = tmp_path / "demo.rcm.json"
    project_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    assert presentation_modus_needs_rebuild(project, project_path, MODE_LCC) is False
