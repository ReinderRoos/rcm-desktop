"""Slice 74 issue 02 — NB-combo zichtbaar + gedeeld in FM-detail-modus (pytest-qt)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from rcm_core.config import RCMConfig
from rcm_core.effect_impact_service import (
    EffectNbFilterSet,
    EffectPresentation,
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
from rcm_desktop.adapter.fm_results_table_model import RAW_ROLE
from rcm_desktop.adapter.run_service import build_run_result

from tests.test_desktop_results_workspace_window import _ensure_app
from tests.workspace_test_helpers import switch_workspace_modus

NUM = 5
_DOWNTIME_COL = 6
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
                is_evident=True,
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


def _window_in_fm_detail(monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _project()
    window._state.set_last_project(project)
    window._state.set_last_run(build_run_result(project, [_fmr()]))
    app.processEvents()
    switch_workspace_modus(window, "fm_detail", app)
    app.processEvents()
    return app, window


def test_nb_combo_visible_in_fm_detail_mode(monkeypatch):
    _app, window = _window_in_fm_detail(monkeypatch)
    assert window.nb_effect_filter_combo.isVisible() is True


def _downtime_raw(window) -> float:
    model = window.fm_table_view.model()
    for r in range(model.rowCount()):
        return float(model.data(model.index(r, _DOWNTIME_COL), RAW_ROLE))
    raise AssertionError("geen FM-rijen")


def test_nb_filter_change_in_fm_detail_rerenders_downtime(monkeypatch):
    from rcm_desktop.adapter.results_workspace_state import ContributionPresentation

    app, window = _window_in_fm_detail(monkeypatch)
    window.workspace_state.set_contribution_presentation(
        ContributionPresentation(horizon="lifecycle")
    )
    app.processEvents()
    before = _downtime_raw(window)
    assert before == pytest.approx(10.0, abs=1e-9)

    window.workspace_state.set_effect_nb_filter(_filter("AV-1"))
    app.processEvents()

    after = _downtime_raw(window)
    expected = nb_scalar_for_fm(_project(), _fmr(), nb_filter=_filter("AV-1"), presentation=_LIFECYCLE_HOURS)
    assert after == pytest.approx(expected, abs=1e-9)
    assert after < before


def test_inspector_visible_and_refreshed_on_filter_change(monkeypatch):
    app, window = _window_in_fm_detail(monkeypatch)
    window.fm_table_view.selectRow(0)
    app.processEvents()
    assert window.fm_inspector_panel.isVisible() is True
    window.workspace_state.set_effect_nb_filter(_filter("AV-1"))
    app.processEvents()
    assert window.fm_inspector_panel.isVisible() is True


def test_nb_filter_selection_shared_with_top10(monkeypatch):
    app, window = _window_in_fm_detail(monkeypatch)
    window.workspace_state.set_effect_nb_filter(_filter("AV-1"))
    app.processEvents()
    switch_workspace_modus(window, "bijdragen", app)
    app.processEvents()
    assert window.workspace_state.snapshot().effect_nb_filter == _filter("AV-1")
