"""Slice 71 — Top 10 metric 3-way + NB-effectfilter (vervangt slice 70 effectklasse)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_desktop.adapter.contribution_chart_service import build_contribution_rows
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_NIET_BESCHIKBAARHEID,
    ResultsWorkspaceState,
    SOURCE_PBS,
    normalize_metric,
    normalize_source,
)
from rcm_core.effect_impact_service import EffectNbFilterSet
from rcm_core.incremental_run import run_incremental_analysis
from rcm_desktop.adapter.isograph_import_service import build_from_workbook
from rcm_desktop.adapter.run_service import build_run_result

CM_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_CM.xlsx"


def test_legacy_effectklasse_source_normalizes_to_pbs() -> None:
    assert normalize_source("effectklasse") == SOURCE_PBS


def test_legacy_effectimpact_metric_normalizes_to_nb() -> None:
    assert normalize_metric("effectimpact") == METRIC_NIET_BESCHIKBAARHEID


def test_workspace_state_starts_with_empty_nb_filter() -> None:
    state = ResultsWorkspaceState()
    assert state.snapshot().effect_nb_filter.is_all()


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_top10_pbs_nb_with_effect_filter() -> None:
    result = build_from_workbook(CM_FIXTURE, modeljaar=2026)
    run_out = run_incremental_analysis(
        result.project,
        CM_FIXTURE.with_suffix(".rcm.cache.json"),
        full_recompute=True,
        parallel=False,
    )
    run = build_run_result(result.project, list(run_out.fm_results.values()))
    schutten = "Schutten 0-20% functieverlies"
    filt = EffectNbFilterSet(selected_klasse_ids=frozenset({schutten}))
    rows = build_contribution_rows(
        result.project,
        run,
        source=SOURCE_PBS,
        metric=METRIC_NIET_BESCHIKBAARHEID,
        top_n=5,
        scope_id=None,
        effect_nb_filter=filt,
    )
    assert len(rows) == 5
    assert all(r.share_pct > 0.0 for r in rows)
