from __future__ import annotations

import pytest

from rcm_desktop.adapter.results_workspace_state import (
    ContributionPresentation,
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    MODE_LCC,
    SOURCE_FAALWIJZE,
    SOURCE_PBS,
    ResultsWorkspaceState,
    normalize_metric,
    normalize_modus,
)


def test_default_snapshot_is_fm_detail_pbs_no_scope():
    state = ResultsWorkspaceState()
    snap = state.snapshot()

    assert snap.modus == MODE_FM_DETAIL
    assert snap.source == SOURCE_PBS
    assert snap.metric == METRIC_NIET_BESCHIKBAARHEID
    assert snap.top_n == 10
    assert snap.scope_id is None
    assert snap.filter_text == ""
    assert snap.contribution_presentation == ContributionPresentation()
    assert snap.active_view_id == "output.fm_results"


def test_subscribe_receives_snapshot_on_every_setter_call():
    state = ResultsWorkspaceState()
    seen: list = []
    state.subscribe(seen.append)

    state.set_modus(MODE_LCC)

    assert len(seen) == 1
    assert seen[0].modus == MODE_LCC


def test_set_modus_rejects_unknown_modus():
    state = ResultsWorkspaceState()

    with pytest.raises(ValueError):
        state.set_modus("kabouters")


def test_legacy_modus_migrates_to_active_modi():
    state = ResultsWorkspaceState()
    state.set_modus("preventief_onderhoud")
    assert state.snapshot().modus == MODE_LCC
    state.set_modus("niet_beschikbaarheid")
    assert state.snapshot().modus == MODE_FM_DETAIL
    state.set_modus(MODE_BIJDRAGEN)
    assert state.snapshot().modus == MODE_FM_DETAIL


def test_normalize_modus_maps_legacy_strings():
    assert normalize_modus("preventief_onderhoud") == MODE_LCC
    assert normalize_modus("niet_beschikbaarheid") == MODE_FM_DETAIL
    assert normalize_modus(MODE_BIJDRAGEN) == MODE_FM_DETAIL
    assert normalize_modus(MODE_FM_DETAIL) == MODE_FM_DETAIL


def test_normalize_metric_maps_risico_and_downtime():
    assert normalize_metric("risico") == METRIC_NIET_BESCHIKBAARHEID
    assert normalize_metric("downtime") == METRIC_NIET_BESCHIKBAARHEID


def test_set_metric_migrates_legacy_risico():
    state = ResultsWorkspaceState()
    state.set_metric("risico")
    assert state.snapshot().metric == METRIC_NIET_BESCHIKBAARHEID


def test_pbs_scope_survives_modus_switch():
    state = ResultsWorkspaceState()
    state.set_scope("PBS-42")

    state.set_modus(MODE_LCC)
    state.set_modus(MODE_FM_DETAIL)

    assert state.snapshot().scope_id == "PBS-42"


def test_source_is_sticky_per_modus():
    state = ResultsWorkspaceState()
    state.set_source(SOURCE_FAALWIJZE)

    state.set_modus(MODE_LCC)
    assert state.snapshot().source == SOURCE_PBS

    state.set_modus(MODE_FM_DETAIL)
    assert state.snapshot().source == SOURCE_FAALWIJZE


def test_metric_is_sticky_across_modus_switches():
    state = ResultsWorkspaceState()
    state.set_metric(METRIC_KOSTEN)

    state.set_modus(MODE_LCC)
    state.set_modus(MODE_FM_DETAIL)

    assert state.snapshot().metric == METRIC_KOSTEN


def test_contribution_presentation_sticks_across_modus_switches():
    state = ResultsWorkspaceState()
    pres = ContributionPresentation(horizon="lifecycle", unavailability_display="percent")
    state.set_contribution_presentation(pres)
    state.set_modus(MODE_LCC)
    state.set_modus(MODE_FM_DETAIL)
    assert state.snapshot().contribution_presentation == pres


def test_reset_for_new_project_returns_to_factory_defaults():
    state = ResultsWorkspaceState()
    state.set_modus(MODE_LCC)
    state.set_metric(METRIC_KOSTEN)
    state.set_contribution_horizon("lifecycle")
    state.set_scope("PBS-9")
    state.set_filter_text("foo")

    state.reset_for_new_project()
    snap = state.snapshot()

    assert snap.modus == MODE_FM_DETAIL
    assert snap.metric == METRIC_NIET_BESCHIKBAARHEID
    assert snap.contribution_presentation == ContributionPresentation()
