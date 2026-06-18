"""Slice 74 issue 01 — Qt-vrije FM-rij-filter-helper.

De downtime-kolom van de FM-detail-tabel respecteert de NB-effectfilter op
render-tijd. Lege filter = ongewijzigd; gevulde filter vervangt de
downtime-kolom door `nb_scalar_for_fm` (lifecycle/uren). Geen QApplication.
"""

from __future__ import annotations

import pytest

from rcm_core.config import RCMConfig
from rcm_core.effect_impact_service import (
    EffectNbFilterSet,
    EffectPresentation,
    HIDDEN_NB_RESTPOST_ID,
    nb_scalar_for_fm,
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
from rcm_desktop.adapter.result_view_service import (
    apply_nb_filter_to_fm_rows,
    build_rows,
)

NUM = 5
DOWNTIME_HR = 10.0
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
        total_cost_eur=123.0,
        risk_contribution=0.0,
        fm_effect_bijdragen={"AV-1": 0.5, "AV-2": 0.25},
        fm_effect_bijdragen_per_jaar={"AV-1": [0.1] * NUM, "AV-2": [0.05] * NUM},
        horizon_profile=FMHorizonProfile(
            cor_eur=[0.0] * NUM,
            cor_downtime_hr=[1.5] * NUM,
            hidden_nb_hr=[0.5] * NUM,
        ),
    )


def _filter(*ids: str) -> EffectNbFilterSet:
    return EffectNbFilterSet(selected_klasse_ids=frozenset(ids))


def test_empty_filter_leaves_rows_unchanged() -> None:
    project, fmr = _project(), _fmr()
    rows = build_rows(project, [fmr])
    out = apply_nb_filter_to_fm_rows(project, [fmr], rows, EffectNbFilterSet())
    assert tuple(out) == tuple(rows)


def test_filled_filter_replaces_downtime_with_nb_scalar() -> None:
    project, fmr = _project(), _fmr()
    rows = build_rows(project, [fmr])
    filt = _filter("AV-1")
    out = apply_nb_filter_to_fm_rows(project, [fmr], rows, filt)
    expected = nb_scalar_for_fm(project, fmr, nb_filter=filt, presentation=_LIFECYCLE_HOURS)
    row = next(r for r in out if r.fm_id == "FM-1")
    assert row.expected_total_downtime_hr == pytest.approx(expected, abs=1e-9)


def test_filtered_downtime_never_exceeds_total() -> None:
    project, fmr = _project(), _fmr()
    rows = build_rows(project, [fmr])
    total = nb_scalar_for_fm(project, fmr, nb_filter=EffectNbFilterSet(), presentation=_LIFECYCLE_HOURS)
    for filt in (_filter("AV-1"), _filter("AV-2"), _filter(HIDDEN_NB_RESTPOST_ID)):
        out = apply_nb_filter_to_fm_rows(project, [fmr], rows, filt)
        row = next(r for r in out if r.fm_id == "FM-1")
        assert row.expected_total_downtime_hr <= total + 1e-9


def test_all_posts_partition_equals_total() -> None:
    project, fmr = _project(), _fmr()
    rows = build_rows(project, [fmr])
    total = nb_scalar_for_fm(project, fmr, nb_filter=EffectNbFilterSet(), presentation=_LIFECYCLE_HOURS)
    all_posts = _filter("AV-1", "AV-2", HIDDEN_NB_RESTPOST_ID)
    out = apply_nb_filter_to_fm_rows(project, [fmr], rows, all_posts)
    row = next(r for r in out if r.fm_id == "FM-1")
    assert row.expected_total_downtime_hr == pytest.approx(total, abs=1e-9)


def test_other_columns_unchanged_under_filter() -> None:
    project, fmr = _project(), _fmr()
    rows = build_rows(project, [fmr])
    out = apply_nb_filter_to_fm_rows(project, [fmr], rows, _filter("AV-1"))
    row = next(r for r in out if r.fm_id == "FM-1")
    base = next(r for r in rows if r.fm_id == "FM-1")
    assert row.expected_failures == base.expected_failures
    assert row.total_cost_eur == base.total_cost_eur
    assert row.faalwijze_omschrijving == base.faalwijze_omschrijving
    assert row.pbs_id == base.pbs_id


def test_row_without_matching_fm_result_is_kept() -> None:
    project, fmr = _project(), _fmr()
    rows = build_rows(project, [fmr])
    out = apply_nb_filter_to_fm_rows(project, [], rows, _filter("AV-1"))
    assert tuple(out) == tuple(rows)


# --- Adapter-seam: build_fm_detail_view ------------------------------------


def _session(project: RCMProject, fm_results: list[FMResult]):
    from rcm_desktop.adapter.loaded_project import LoadedProject
    from rcm_desktop.adapter.project_session import ProjectSession
    from rcm_desktop.adapter.run_service import build_run_result

    run = build_run_result(project, fm_results)
    loaded = LoadedProject.from_core(project)
    return ProjectSession.from_parts(loaded, run=run)


def test_build_fm_detail_view_applies_active_nb_filter() -> None:
    from rcm_desktop.adapter.results_workspace_state import (
        ContributionPresentation,
        MODE_FM_DETAIL,
        ResultsWorkspaceState,
    )
    from rcm_desktop.adapter.workspace_view_service import build_fm_detail_view

    project, fmr = _project(), _fmr()
    session = _session(project, [fmr])
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_FM_DETAIL)
    ws.set_contribution_presentation(ContributionPresentation(horizon="lifecycle"))
    ws.set_effect_nb_filter(_filter("AV-1"))
    view = build_fm_detail_view(session, ws.snapshot())

    assert view is not None
    row = next(r for r in view.fm_rows if r.fm_id == "FM-1")
    expected = nb_scalar_for_fm(project, fmr, nb_filter=_filter("AV-1"), presentation=_LIFECYCLE_HOURS)
    assert row.expected_total_downtime_hr == pytest.approx(expected, abs=1e-9)


def test_build_fm_detail_view_empty_filter_keeps_motor_downtime() -> None:
    from rcm_desktop.adapter.results_workspace_state import (
        ContributionPresentation,
        MODE_FM_DETAIL,
        ResultsWorkspaceState,
    )
    from rcm_desktop.adapter.workspace_view_service import build_fm_detail_view

    project, fmr = _project(), _fmr()
    session = _session(project, [fmr])
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_FM_DETAIL)
    ws.set_contribution_presentation(ContributionPresentation(horizon="lifecycle"))
    view = build_fm_detail_view(session, ws.snapshot())

    assert view is not None
    row = next(r for r in view.fm_rows if r.fm_id == "FM-1")
    assert row.expected_total_downtime_hr == pytest.approx(fmr.expected_total_downtime_hr, abs=1e-9)
