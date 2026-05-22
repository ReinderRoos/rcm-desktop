"""Slice 37 performance contracts — contribution-only post-run presentatie.

Run: pytest -m perf tests/perf/test_slice37_regression.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from rcm_core.persistence import load_project
from rcm_desktop.adapter.presentation_cache_service import build_contribution_presentation

PERF_DIR = Path(__file__).parent
BASELINE_PATH = PERF_DIR / "baseline.json"
FIXTURE = Path("tests/fixtures/sample_project.rcm.json")


@pytest.fixture(scope="module")
def baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def contracts(baseline: dict) -> dict:
    section = baseline.get("slice37_contracts")
    assert section is not None, "baseline.json missing slice37_contracts"
    return section


@pytest.mark.perf
def test_post_run_presentation_skips_legacy_builders(monkeypatch, contracts: dict) -> None:
    """Post-run presentatie roept geen LCC/NB/PM builders aan (slice 37)."""
    project = load_project(FIXTURE)
    from rcm_desktop.adapter.run_service import RunMetrics, RunResult

    run = RunResult(
        status="done",
        summary="klaar",
        metrics=RunMetrics(fm_result_count=1, total_lifecycle_faalmomenten=1.0, total_cost_eur=1.0),
        fm_core_results=(),
    )
    counts = {"lcc": 0, "nb": 0, "pm": 0, "contrib": 0}

    import rcm_desktop.adapter.lcc_chart_service as lcc_mod
    import rcm_desktop.adapter.pm_chart_service as pm_mod
    import rcm_desktop.adapter.presentation_cache_service as pc_mod
    import rcm_desktop.adapter.unavailability_chart_service as nb_mod

    real_contrib = pc_mod.build_contribution_presentation

    def spy_contrib(*args, **kwargs):
        counts["contrib"] += 1
        return real_contrib(*args, **kwargs)

    monkeypatch.setattr(pc_mod, "build_contribution_presentation", spy_contrib)
    monkeypatch.setattr(lcc_mod, "build_single_run_lcc_input", lambda *_a, **_k: counts.__setitem__("lcc", counts["lcc"] + 1))
    monkeypatch.setattr(nb_mod, "build_unavailability_chart_input", lambda *_a, **_k: counts.__setitem__("nb", counts["nb"] + 1))
    monkeypatch.setattr(pm_mod, "build_pm_chart_input", lambda *_a, **_k: counts.__setitem__("pm", counts["pm"] + 1))

    from rcm_desktop.adapter.presentation_cache_service import build_project_total_presentation

    build_project_total_presentation(project, run)

    assert counts["contrib"] <= contracts["post_run_contribution_builds_max"]
    assert counts["lcc"] <= contracts["post_run_lcc_builds_max"]
    assert counts["nb"] <= contracts["post_run_nb_builds_max"]
    assert counts["pm"] <= contracts["post_run_pm_builds_max"]


@pytest.mark.perf
def test_contribution_presentation_has_bijdragen_modus_only(contracts: dict) -> None:
    project = load_project(FIXTURE)
    from rcm_desktop.adapter.run_service import run

    run_result = run(project, FIXTURE)
    assert run_result.status == "done"
    dto = build_contribution_presentation(project, run_result)
    assert dto.built_modi == frozenset({"bijdragen"})
    assert len(dto.contribution_rows) > 0
