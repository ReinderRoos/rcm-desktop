"""Slice 71 — NB-effectfilter deep module + workspace integratie."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.effect_impact_service import (
    EffectNbFilterSet,
    EffectPresentation,
    aggregate,
    list_nb_effect_klassen,
    nb_scalar_for_fm,
    nb_yearly_series,
)
from rcm_core.effect_taxonomy import CATEGORIE_BESCHIKBAARHEID, CATEGORIE_VEILIGHEID
from rcm_core.incremental_run import run_incremental_analysis
from rcm_desktop.adapter.contribution_horizon_value_service import contribution_value_for_fm
from rcm_desktop.adapter.contribution_chart_service import build_contribution_rows
from rcm_desktop.adapter.isograph_import_service import build_from_workbook
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    ResultsWorkspaceState,
    SOURCE_PBS,
    normalize_metric,
    normalize_source,
)
from rcm_desktop.adapter.run_service import build_run_result

CM_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_CM.xlsx"
GOLDEN_CAUSE = "06H-350.1.1.1.1.1.A.1"
SCHUTTEN_020 = "Schutten 0-20% functieverlies"


@pytest.fixture(scope="module")
def cm_run():
    if not CM_FIXTURE.is_file():
        pytest.skip("CM fixture ontbreekt")
    result = build_from_workbook(CM_FIXTURE, modeljaar=2026)
    run_out = run_incremental_analysis(
        result.project,
        CM_FIXTURE.with_suffix(".rcm.cache.json"),
        full_recompute=True,
        parallel=False,
    )
    return result.project, build_run_result(result.project, list(run_out.fm_results.values()))


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_empty_nb_filter_matches_total_nb_scalar(cm_run) -> None:
    project, run = cm_run
    fmr = next(fr for fr in run.fm_core_results if fr.fm_id == GOLDEN_CAUSE)
    from rcm_desktop.adapter.results_workspace_state import ContributionPresentation

    pres = ContributionPresentation(horizon="lifecycle")
    expected = contribution_value_for_fm(
        project, fmr, metric=METRIC_NIET_BESCHIKBAARHEID, presentation=pres
    )
    got = nb_scalar_for_fm(
        project,
        fmr,
        nb_filter=EffectNbFilterSet(),
        presentation=EffectPresentation(horizon="lifecycle"),
    )
    assert got == pytest.approx(expected, rel=1e-6)


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_filtered_nb_scalar_bounded_by_total_and_aggregate(cm_run) -> None:
    """Slice 73 / ADR-0010: een deelselectie is per-bucket geclamped op het totaal.

    De gefilterde NB volgt uit de bucketreeks-spine en mag het totaal nooit
    overschrijden (geheel >= delen), ook niet als de aggregate-klassewaarde dat
    door RF-overlap (Sigma RF > 1) wel zou doen.
    """
    project, run = cm_run
    fmr = next(fr for fr in run.fm_core_results if fr.fm_id == GOLDEN_CAUSE)
    rows = aggregate(
        project,
        (fmr,),
        fm_ids=frozenset({GOLDEN_CAUSE}),
        categorie_filter=CATEGORIE_BESCHIKBAARHEID,
    )
    row = next(r for r in rows if r.klasse_id == SCHUTTEN_020)
    filt = EffectNbFilterSet(selected_klasse_ids=frozenset({SCHUTTEN_020}))
    got = nb_scalar_for_fm(project, fmr, nb_filter=filt)
    total = nb_scalar_for_fm(project, fmr, nb_filter=EffectNbFilterSet())
    assert got > 0.0
    assert got <= total + 1e-6
    assert got <= row.waarde_totaal + 1e-6


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_list_nb_effect_klassen_excludes_veiligheid(cm_run) -> None:
    project, _run = cm_run
    nb_ids = {kid for kid, _ in list_nb_effect_klassen(project)}
    for ek in project.effect_klassen.values():
        if ek.klasse_id in nb_ids:
            assert CATEGORIE_BESCHIKBAARHEID in ek.categorie.lower()
        if CATEGORIE_VEILIGHEID in ek.categorie.lower():
            assert ek.klasse_id not in nb_ids


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_filtered_top10_pbs_ranking_share_pct(cm_run) -> None:
    project, run = cm_run
    filt = EffectNbFilterSet(selected_klasse_ids=frozenset({SCHUTTEN_020}))
    rows = build_contribution_rows(
        project,
        run,
        source=SOURCE_PBS,
        metric=METRIC_NIET_BESCHIKBAARHEID,
        top_n=10,
        scope_id=None,
        effect_nb_filter=filt,
    )
    assert rows
    assert all(r.share_pct > 0.0 for r in rows)
    assert sum(r.value for r in rows) > 0.0


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_nb_yearly_series_reconciles_to_lifecycle_scalar(cm_run) -> None:
    project, run = cm_run
    fm_dict = {fr.fm_id: fr for fr in run.fm_core_results}
    fmr = next(fr for fr in run.fm_core_results if fr.fm_id == GOLDEN_CAUSE)
    series = nb_yearly_series(project, fm_dict, nb_filter=EffectNbFilterSet(), fm_ids=frozenset({GOLDEN_CAUSE}))
    scalar = nb_scalar_for_fm(project, fmr, nb_filter=EffectNbFilterSet())
    assert sum(series) == pytest.approx(scalar, rel=0.05)


def test_workspace_legacy_effectklasse_normalizes() -> None:
    assert normalize_source("effectklasse") == SOURCE_PBS
    assert normalize_metric("effectimpact") == METRIC_NIET_BESCHIKBAARHEID


def test_workspace_state_effect_nb_filter() -> None:
    state = ResultsWorkspaceState()
    filt = EffectNbFilterSet(selected_klasse_ids=frozenset({"k1"}))
    seen: list[object] = []
    state.subscribe(lambda s: seen.append(s.effect_nb_filter))
    state.set_effect_nb_filter(filt)
    assert state.snapshot().effect_nb_filter == filt
    assert seen[-1] == filt


def test_all_metrics_has_three_entries() -> None:
    from rcm_desktop.adapter.results_workspace_state import ALL_METRICS

    assert set(ALL_METRICS) == {
        METRIC_NIET_BESCHIKBAARHEID,
        METRIC_FAALMOMENTEN,
        METRIC_KOSTEN,
    }
