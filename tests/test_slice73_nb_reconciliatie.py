"""Slice 73 — NB-scalar reconciliatie: bucketreeks-spine, restpost, partitie.

Qt-vrije seam-tests op `rcm_core.effect_impact_service` + de Bug 1-mapping in
de Top 10-adapter. Programmatische fixtures (geen Excel) zodat ze altijd draaien.
"""

from __future__ import annotations

import math

import pytest

from rcm_core.config import RCMConfig
from rcm_core.effect_impact_service import (
    EffectNbFilterSet,
    EffectPresentation,
    HIDDEN_NB_RESTPOST_ID,
    aggregate,
    list_nb_effect_klassen,
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

NUM = 5
DOWNTIME_HR = 10.0


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
                downtime_per_failure=TimeDuration(DOWNTIME_HR, TimeUnit.HOURS),
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
            cor_downtime_hr=[1.5] * NUM,
            hidden_nb_hr=[0.5] * NUM,
        ),
    )


def _empty() -> EffectNbFilterSet:
    return EffectNbFilterSet()


def _filter(*ids: str) -> EffectNbFilterSet:
    return EffectNbFilterSet(selected_klasse_ids=frozenset(ids))


# --- Issue 01: spine + Bug 1 -------------------------------------------------


def test_filtered_average_is_year_mean_not_lifecycle_total() -> None:
    """Bug 1: '\u00d8 per jaar' gefilterd is het jaargemiddelde, niet het levensduur-totaal."""
    project, fmr = _project(), _fmr()
    pres = EffectPresentation(horizon="per_year", year_index=None)
    got = nb_scalar_for_fm(project, fmr, nb_filter=_filter("AV-1"), presentation=pres)
    assert got == pytest.approx(1.0, abs=1e-9)  # mean van [1.0]*5, niet 5.0


def test_subset_never_exceeds_total_for_every_presentation() -> None:
    project, fmr = _project(), _fmr()
    presentations = [
        EffectPresentation(horizon="lifecycle"),
        EffectPresentation(horizon="lifecycle", unavailability_display="percent"),
        EffectPresentation(horizon="per_year", year_index=None),
        EffectPresentation(horizon="per_year", year_index=0),
        EffectPresentation(horizon="per_year", year_index=2, unavailability_display="percent"),
    ]
    for pres in presentations:
        total = nb_scalar_for_fm(project, fmr, nb_filter=_empty(), presentation=pres)
        for subset in (_filter("AV-1"), _filter("AV-2"), _filter("AV-1", "AV-2")):
            sub = nb_scalar_for_fm(project, fmr, nb_filter=subset, presentation=pres)
            assert sub <= total + 1e-9, (pres, subset)


def test_scalar_is_reduction_of_yearly_series() -> None:
    project, fmr = _project(), _fmr()
    fm_dict = {fmr.fm_id: fmr}
    for filt in (_empty(), _filter("AV-1"), _filter("AV-1", "AV-2")):
        series = nb_yearly_series(project, fm_dict, nb_filter=filt)
        life = nb_scalar_for_fm(project, fmr, nb_filter=filt, presentation=EffectPresentation("lifecycle"))
        avg = nb_scalar_for_fm(project, fmr, nb_filter=filt, presentation=EffectPresentation("per_year", year_index=None))
        yr2 = nb_scalar_for_fm(project, fmr, nb_filter=filt, presentation=EffectPresentation("per_year", year_index=2))
        assert life == pytest.approx(sum(series), abs=1e-9)
        assert avg == pytest.approx(sum(series) / len(series), abs=1e-9)
        assert yr2 == pytest.approx(series[2], abs=1e-9)


def test_effect_presentation_average_maps_to_per_year() -> None:
    """Bug 1-bron: ContributionPresentation '\u00d8 per jaar' mag niet platgeslagen worden."""
    from rcm_desktop.adapter.contribution_horizon_value_service import (
        effect_presentation_for_contribution,
    )
    from rcm_desktop.adapter.results_workspace_state import ContributionPresentation

    project = _project()
    pres = ContributionPresentation(horizon="per_year", year_choice="average")
    eff = effect_presentation_for_contribution(project, pres)
    assert eff.horizon == "per_year"
    assert eff.year_index is None


# --- Issue 02: restpost + partitie + PM-eenheid ------------------------------


def test_restpost_listed_as_selectable_post() -> None:
    project = _project()
    ids = {kid for kid, _ in list_nb_effect_klassen(project)}
    assert HIDDEN_NB_RESTPOST_ID in ids


def test_all_posts_selected_equals_total() -> None:
    project, fmr = _project(), _fmr()
    fm_dict = {fmr.fm_id: fmr}
    all_posts = _filter("AV-1", "AV-2", HIDDEN_NB_RESTPOST_ID)
    for pres in (
        EffectPresentation(horizon="lifecycle"),
        EffectPresentation(horizon="per_year", year_index=None),
        EffectPresentation(horizon="per_year", year_index=1),
    ):
        total = nb_scalar_for_fm(project, fmr, nb_filter=_empty(), presentation=pres)
        full = nb_scalar_for_fm(project, fmr, nb_filter=all_posts, presentation=pres)
        assert full == pytest.approx(total, abs=1e-9), pres
    series_total = nb_yearly_series(project, fm_dict, nb_filter=_empty())
    series_full = nb_yearly_series(project, fm_dict, nb_filter=all_posts)
    assert series_full == pytest.approx(series_total, abs=1e-9)


def test_restpost_absorbs_hidden_nb() -> None:
    project, fmr = _project(), _fmr()
    rest = nb_scalar_for_fm(
        project, fmr, nb_filter=_filter(HIDDEN_NB_RESTPOST_ID),
        presentation=EffectPresentation("lifecycle"),
    )
    # totaal (10) - reele availability (AV-1 5 + AV-2 2.5 = 7.5) = 2.5 hidden NB
    assert rest == pytest.approx(2.5, abs=1e-9)


def test_pm_contribution_reported_in_hours_without_double_downtime() -> None:
    """pm_effect_bijdragen is in de motor al uren (duration x RF x executions).

    De availability-rij telt CM (telling x downtime) + PM (reeds uren); PM mag
    NIET nogmaals met downtime worden vermenigvuldigd.
    """
    project = _project()
    project.faalwijzes["FM-1"].downtime_per_failure = TimeDuration(4.0, TimeUnit.HOURS)
    fmr = _fmr()  # AV-1 CM lifecycle 0.5 -> 0.5*4 = 2.0 uren
    fmr.pm_effect_bijdragen = {"AV-1": 3.0}  # reeds uren
    rows = aggregate(
        project, (fmr,), fm_ids=frozenset({"FM-1"}),
        categorie_filter=CATEGORIE_BESCHIKBAARHEID,
    )
    row = next(r for r in rows if r.klasse_id == "AV-1")
    assert row.eenheid == "uren"
    assert row.waarde_pm == pytest.approx(3.0, abs=1e-9)  # uren, niet x downtime
    assert row.waarde_cm == pytest.approx(2.0, abs=1e-9)


# --- Issue 03: per-FM downtime_hr in aggregate -------------------------------


def test_aggregate_uses_per_fm_downtime_for_shared_klasse() -> None:
    project = _project()
    project.faalwijzes["FM-2"] = Faalwijze(
        fm_id="FM-2", pbs_id="PBS-1", functie_id="F",
        faalwijze_omschrijving="Test 2", mttf_jaar=10.0,
        downtime_per_failure=TimeDuration(2.0, TimeUnit.HOURS),
    )
    fmr1 = _fmr()  # downtime 10, AV-1 lifecycle cm_raw 0.5 -> 5.0 uren
    fmr2 = FMResult(
        fm_id="FM-2", pbs_id="PBS-1",
        p_failure_lifecycle=0.5, expected_failures=1.0,
        expected_raw_downtime_hr=2.0, expected_detection_delay_hr=0.0,
        expected_total_downtime_hr=2.0, expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=0.0, pm_cost_eur=0.0, total_cost_eur=0.0,
        risk_contribution=0.0,
        fm_effect_bijdragen={"AV-1": 1.0},  # downtime 2 -> 2.0 uren
        fm_effect_bijdragen_per_jaar={"AV-1": [0.2] * NUM},
    )
    rows = aggregate(
        project, (fmr1, fmr2), fm_ids=frozenset({"FM-1", "FM-2"}),
        categorie_filter=CATEGORIE_BESCHIKBAARHEID,
    )
    row = next(r for r in rows if r.klasse_id == "AV-1")
    # per-FM: 0.5*10 + 1.0*2 = 7.0 uren (niet 1.5 * downtime_van_eerste_FM)
    assert row.waarde_cm == pytest.approx(7.0, abs=1e-9)


# --- Issue 04: Effectfilter-leesbaarheid (views) -----------------------------


def test_filter_combo_shows_full_labels_and_restpost() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from tests.test_desktop_results_workspace_window import _ensure_app
    from rcm_desktop.views.widgets.nb_effect_filter_combo import NbEffectFilterCombo

    _ensure_app()
    project = _project()
    combo = NbEffectFilterCombo()
    combo.set_klassen(list_nb_effect_klassen(project))

    model = combo.model()
    labels = [model.item(r).text() for r in range(model.rowCount())]
    tooltips = [model.item(r).toolTip() for r in range(model.rowCount())]
    ids = [str(model.item(r).data(Qt.UserRole)) for r in range(model.rowCount())]

    assert HIDDEN_NB_RESTPOST_ID in ids
    assert all(tt for tt in tooltips)  # elke regel heeft een volledige tooltip
    assert tooltips == labels
    assert combo.view().minimumWidth() >= combo.minimumWidth()

