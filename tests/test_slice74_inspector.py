"""Slice 74 issue 03 — FM-inspector reflecteert NB-filter (Qt-vrij)."""

from __future__ import annotations

import pytest

from rcm_core.config import RCMConfig
from rcm_core.effect_impact_service import (
    EffectNbFilterSet,
    EffectPresentation,
    nb_scalar_for_fm,
    nb_yearly_series,
)
from rcm_core.effect_taxonomy import CATEGORIE_BESCHIKBAARHEID
from rcm_core.models import (
    EffectKlasse,
    FMEffectLink,
    FMHorizonProfile,
    FMResult,
    Faalwijze,
    PBSItem,
    RCMProject,
)
from rcm_core.units import TimeDuration, TimeUnit
from rcm_desktop.adapter.fm_verification_service import build_fm_verification_view

NUM = 5
_LIFECYCLE_HOURS = EffectPresentation(horizon="lifecycle", unavailability_display="hours")


def _project() -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=float(NUM), modeljaar=2020),
        pbs_items={"PBS-1": PBSItem("PBS-1", "o", "e", "Pomp")},
        faalwijzes={
            "FM-1": Faalwijze(
                fm_id="FM-1",
                pbs_id="PBS-1",
                functie_id="F",
                faalwijze_omschrijving="Test",
                mttf_jaar=10.0,
                downtime_per_failure=TimeDuration(10.0, TimeUnit.HOURS),
            ),
        },
        effect_klassen={
            "AV-1": EffectKlasse("AV-1", "Roldeur volledig gestremd", "F", CATEGORIE_BESCHIKBAARHEID),
            "AV-2": EffectKlasse("AV-2", "Roldeur deels gestremd", "F", CATEGORIE_BESCHIKBAARHEID),
        },
        fm_effect_links={
            "L1": FMEffectLink("L1", "FM-1", "AV-1", 0.6),
            "L2": FMEffectLink("L2", "FM-1", "AV-2", 0.4),
        },
    )


def _fmr() -> FMResult:
    return FMResult(
        fm_id="FM-1",
        pbs_id="PBS-1",
        p_failure_lifecycle=0.5,
        expected_failures=0.75,
        expected_raw_downtime_hr=7.5,
        expected_detection_delay_hr=2.5,
        expected_total_downtime_hr=10.0,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=0.0,
        pm_cost_eur=0.0,
        total_cost_eur=0.0,
        risk_contribution=0.0,
        fm_effect_bijdragen={"AV-1": 0.5, "AV-2": 0.25},
        fm_effect_bijdragen_per_jaar={"AV-1": [0.1] * NUM, "AV-2": [0.05] * NUM},
        horizon_profile=FMHorizonProfile(
            cor_eur=[0.0] * NUM,
            cor_downtime_hr=[2.0] * NUM,
            hidden_nb_hr=[0.5] * NUM,
        ),
    )


def _filter(*ids: str) -> EffectNbFilterSet:
    return EffectNbFilterSet(selected_klasse_ids=frozenset(ids))


def test_empty_filter_lifecycle_identical_to_today() -> None:
    project, fmr = _project(), _fmr()
    base = build_fm_verification_view(project, fmr)
    empty = build_fm_verification_view(project, fmr, nb_filter=EffectNbFilterSet())
    assert empty.lifecycle == base.lifecycle


def test_filled_filter_lifecycle_downtime_is_nb_scalar() -> None:
    project, fmr = _project(), _fmr()
    filt = _filter("AV-1")
    view = build_fm_verification_view(project, fmr, nb_filter=filt)
    expected = nb_scalar_for_fm(project, fmr, nb_filter=filt, presentation=_LIFECYCLE_HOURS)
    assert view.lifecycle.expected_total_downtime_hr == pytest.approx(expected, abs=1e-9)


def test_year_series_reduces_from_nb_bucket_spine() -> None:
    project, fmr = _project(), _fmr()
    filt = _filter("AV-1")
    view = build_fm_verification_view(project, fmr, nb_filter=filt)
    series = nb_yearly_series(project, {fmr.fm_id: fmr}, nb_filter=filt)
    assert [r.nb_downtime_hr for r in view.year_rows] == pytest.approx(series, abs=1e-9)


def test_empty_filter_year_series_equals_total() -> None:
    project, fmr = _project(), _fmr()
    view = build_fm_verification_view(project, fmr)
    total = nb_yearly_series(project, {fmr.fm_id: fmr}, nb_filter=EffectNbFilterSet())
    assert [r.nb_downtime_hr for r in view.year_rows] == pytest.approx(total, abs=1e-9)


def test_reconcile_hash_and_identity_unchanged_under_filter() -> None:
    project, fmr = _project(), _fmr()
    base = build_fm_verification_view(project, fmr)
    filtered = build_fm_verification_view(project, fmr, nb_filter=_filter("AV-1"))
    assert filtered.reconcile_ok == base.reconcile_ok
    assert filtered.reconcile_notes == base.reconcile_notes
    assert filtered.fm_input_hash == base.fm_input_hash
    assert filtered.fm_id == base.fm_id
