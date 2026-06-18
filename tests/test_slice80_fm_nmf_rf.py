"""Slice 80 issue 01 — NMF/RF-kolommen in FM-resultaten-viewbuilder (Qt-vrij)."""

from __future__ import annotations

import pytest

from rcm_core.config import RCMConfig
from rcm_core.effect_impact_service import EffectNbFilterSet
from rcm_core.effect_taxonomy import CATEGORIE_BESCHIKBAARHEID
from rcm_core.models import (
    EffectKlasse,
    FMEffectLink,
    FMResult,
    Faalwijze,
    PBSItem,
    RCMProject,
)
from rcm_core.units import TimeDuration, TimeUnit
from rcm_desktop.adapter.result_view_service import (
    build_rows,
    enrich_fm_rows_with_nmf_rf,
)


def _project(*, fm_evident: bool = True) -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=5.0, modeljaar=2020),
        pbs_items={"PBS-1": PBSItem("PBS-1", "o", "e", "Pomp")},
        faalwijzes={
            "FM-1": Faalwijze(
                fm_id="FM-1",
                pbs_id="PBS-1",
                functie_id="F",
                faalwijze_omschrijving="Test",
                mttf_jaar=10.0,
                downtime_per_failure=TimeDuration(10.0, TimeUnit.HOURS),
                is_evident=fm_evident,
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
        total_cost_eur=123.0,
        risk_contribution=0.0,
    )


def _filter(*ids: str) -> EffectNbFilterSet:
    return EffectNbFilterSet(selected_klasse_ids=frozenset(ids))


def test_single_class_filter_uses_that_fractie() -> None:
    project = _project()
    rows = build_rows(project, [_fmr()])
    out = enrich_fm_rows_with_nmf_rf(project, out=rows, nb_filter=_filter("AV-1"))
    row = out[0]
    assert row.rf == pytest.approx(0.6)
    assert row.rf_tooltip_entries == ()


def test_empty_filter_uses_max_fractie_with_tooltip() -> None:
    project = _project()
    rows = build_rows(project, [_fmr()])
    out = enrich_fm_rows_with_nmf_rf(project, out=rows, nb_filter=EffectNbFilterSet())
    row = out[0]
    assert row.rf == pytest.approx(0.6)
    assert len(row.rf_tooltip_entries) == 2
    by_id = {e.klasse_id: e.fractie for e in row.rf_tooltip_entries}
    assert by_id["AV-1"] == pytest.approx(0.6)
    assert by_id["AV-2"] == pytest.approx(0.4)


def test_multi_class_filter_uses_max_with_full_tooltip() -> None:
    project = _project()
    rows = build_rows(project, [_fmr()])
    out = enrich_fm_rows_with_nmf_rf(
        project, out=rows, nb_filter=_filter("AV-1", "AV-2")
    )
    row = out[0]
    assert row.rf == pytest.approx(0.6)
    assert len(row.rf_tooltip_entries) == 2


def test_nmf_reflects_is_evident() -> None:
    evident = enrich_fm_rows_with_nmf_rf(
        project=_project(fm_evident=True),
        out=build_rows(_project(fm_evident=True), [_fmr()]),
        nb_filter=EffectNbFilterSet(),
    )[0]
    hidden = enrich_fm_rows_with_nmf_rf(
        project=_project(fm_evident=False),
        out=build_rows(_project(fm_evident=False), [_fmr()]),
        nb_filter=EffectNbFilterSet(),
    )[0]
    assert evident.is_nmf is False
    assert hidden.is_nmf is True
