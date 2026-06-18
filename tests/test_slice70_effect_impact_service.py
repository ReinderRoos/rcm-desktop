"""Slice 70 issue 03 — EffectImpactService."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.effect_impact_service import aggregate
from rcm_core.effect_taxonomy import CATEGORIE_BESCHIKBAARHEID, CATEGORIE_VEILIGHEID
from rcm_core.incremental_run import run_incremental_analysis
from rcm_desktop.adapter.isograph_import_service import build_from_workbook

CM_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_CM.xlsx"
GOLDEN_CAUSE = "06H-350.1.1.1.1.1.A.1"


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_golden_cause_four_effect_rows_with_rf_and_units() -> None:
    result = build_from_workbook(CM_FIXTURE, modeljaar=2026)
    run = run_incremental_analysis(
        result.project,
        CM_FIXTURE.with_suffix(".rcm.cache.json"),
        full_recompute=True,
        parallel=False,
    )
    rows = aggregate(
        result.project,
        run.fm_results,
        fm_ids=frozenset({GOLDEN_CAUSE}),
    )
    golden_rows = [r for r in rows if r.klasse_id in {
        "VGM - Effect 3",
        "VGM - Effect 2",
        "Schutten 0-20% functieverlies",
        "Schutten 81-100% functieverlies",
    }]
    assert len(golden_rows) == 4
    rf_by_id = {r.klasse_id: r.rf_display for r in golden_rows}
    assert rf_by_id["VGM - Effect 3"] == "0,1"
    assert rf_by_id["VGM - Effect 2"] == "0,9"
    assert rf_by_id["Schutten 0-20% functieverlies"] == "1"
    assert rf_by_id["Schutten 81-100% functieverlies"] == "0,5"
    vgm = next(r for r in golden_rows if "VGM" in r.klasse_id and "3" in r.klasse_id)
    schutten = next(r for r in golden_rows if "0-20%" in r.klasse_id)
    assert vgm.eenheid == "incidenten"
    assert vgm.categorie == CATEGORIE_VEILIGHEID
    assert schutten.eenheid == "uren"
    assert schutten.categorie == CATEGORIE_BESCHIKBAARHEID
    assert sum(r.share_pct for r in rows) == pytest.approx(100.0, abs=0.01)


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_categorie_filter_limits_rows() -> None:
    result = build_from_workbook(CM_FIXTURE, modeljaar=2026)
    run = run_incremental_analysis(
        result.project,
        CM_FIXTURE.with_suffix(".rcm.cache.json"),
        full_recompute=True,
        parallel=False,
    )
    all_rows = aggregate(result.project, run.fm_results)
    veilig = aggregate(
        result.project,
        run.fm_results,
        categorie_filter=CATEGORIE_VEILIGHEID,
    )
    assert len(veilig) < len(all_rows)
    assert all(r.categorie == CATEGORIE_VEILIGHEID for r in veilig)
