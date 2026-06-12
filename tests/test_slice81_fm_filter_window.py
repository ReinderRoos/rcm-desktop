"""Slice 81 — filterrij in FM-resultaten venster."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit

from rcm_core.config import RCMConfig
from rcm_core.models import FMHorizonProfile, FMResult, Faalwijze, PBSItem, RCMProject
from rcm_core.units import TimeDuration, TimeUnit
from rcm_desktop.adapter.fm_results_filter_policy import (
    FM_COL_BOUWDEEL,
    FM_COL_KOSTEN,
    FM_COL_NMF,
)
from rcm_desktop.adapter.fm_results_table_model import RAW_ROLE
from rcm_desktop.adapter.run_service import build_run_result
from tests.test_slice74_window import _window_in_fm_detail


def _set_text_filter(window, column: int, text: str) -> None:
    editor = window.fm_table_filter_row.editor(column)
    assert isinstance(editor, QLineEdit)
    editor.setText(text)


def _set_bool_filter(window, column: int, required: bool | None) -> None:
    combo = window.fm_table_filter_row.editor(column)
    assert isinstance(combo, QComboBox)
    for idx in range(combo.count()):
        if combo.itemData(idx) == required:
            combo.setCurrentIndex(idx)
            return
    raise AssertionError(f"geen bool-filteroptie voor {required!r}")


def test_bouwdeel_filter_limits_fm_table_rows(monkeypatch) -> None:
    app, window = _window_in_fm_detail(monkeypatch)
    model = window.fm_table_view.model()
    total = model.rowCount()
    assert total >= 1
    _set_text_filter(window, FM_COL_BOUWDEEL, "zzz_geen_match")
    app.processEvents()
    assert model.rowCount() == 0
    window.fm_filter_clear_button.click()
    app.processEvents()
    assert model.rowCount() == total


def test_nmf_filter_shows_only_nmf_rows(monkeypatch) -> None:
    from PySide6.QtWidgets import QMessageBox

    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    from tests.test_desktop_results_workspace_window import _ensure_app
    from tests.workspace_test_helpers import switch_workspace_modus

    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = RCMProject(
        config=RCMConfig(lifecycle_years=5.0, modeljaar=2020),
        pbs_items={"PBS-1": PBSItem("PBS-1", "o", "e", "Pomp")},
        faalwijzes={
            "FM-1": Faalwijze(
                fm_id="FM-1",
                pbs_id="PBS-1",
                functie_id="F",
                faalwijze_omschrijving="Evident",
                mttf_jaar=10.0,
                is_evident=True,
                downtime_per_failure=TimeDuration(1.0, TimeUnit.HOURS),
            ),
            "FM-2": Faalwijze(
                fm_id="FM-2",
                pbs_id="PBS-1",
                functie_id="F",
                faalwijze_omschrijving="NMF",
                mttf_jaar=10.0,
                is_evident=False,
                downtime_per_failure=TimeDuration(1.0, TimeUnit.HOURS),
            ),
        },
    )
    fmrs = [
        FMResult(
            fm_id="FM-1",
            pbs_id="PBS-1",
            p_failure_lifecycle=0.1,
            expected_failures=1.0,
            expected_raw_downtime_hr=1.0,
            expected_detection_delay_hr=0.0,
            expected_total_downtime_hr=1.0,
            expected_pm_downtime_hr=0.0,
            expected_cm_cost_eur=0.0,
            pm_cost_eur=0.0,
            total_cost_eur=50.0,
            risk_contribution=0.0,
            horizon_profile=FMHorizonProfile(
                cor_eur=[0.0] * 5,
                cor_downtime_hr=[0.0] * 5,
                hidden_nb_hr=[0.0] * 5,
            ),
        ),
        FMResult(
            fm_id="FM-2",
            pbs_id="PBS-1",
            p_failure_lifecycle=0.1,
            expected_failures=1.0,
            expected_raw_downtime_hr=1.0,
            expected_detection_delay_hr=0.0,
            expected_total_downtime_hr=1.0,
            expected_pm_downtime_hr=0.0,
            expected_cm_cost_eur=0.0,
            pm_cost_eur=0.0,
            total_cost_eur=200.0,
            risk_contribution=0.0,
            horizon_profile=FMHorizonProfile(
                cor_eur=[0.0] * 5,
                cor_downtime_hr=[0.0] * 5,
                hidden_nb_hr=[0.0] * 5,
            ),
        ),
    ]
    window._state.set_last_project(project)
    window._state.set_last_run(build_run_result(project, fmrs))
    app.processEvents()
    switch_workspace_modus(window, "fm_detail", app)
    app.processEvents()

    model = window.fm_table_view.model()
    assert model.rowCount() == 2
    _set_bool_filter(window, FM_COL_NMF, True)
    app.processEvents()
    assert model.rowCount() == 1
    assert model.data(model.index(0, 0), RAW_ROLE) == "FM-2"


def test_kosten_filter_limits_rows(monkeypatch) -> None:
    from PySide6.QtWidgets import QMessageBox

    from rcm_desktop.adapter.results_workspace_state import ContributionPresentation
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    from tests.test_desktop_results_workspace_window import _ensure_app
    from tests.workspace_test_helpers import switch_workspace_modus

    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = RCMProject(
        config=RCMConfig(lifecycle_years=5.0, modeljaar=2020),
        pbs_items={"PBS-1": PBSItem("PBS-1", "o", "e", "Pomp")},
        faalwijzes={
            "FM-1": Faalwijze(
                fm_id="FM-1",
                pbs_id="PBS-1",
                functie_id="F",
                faalwijze_omschrijving="Goedkoop",
                mttf_jaar=10.0,
                is_evident=True,
                downtime_per_failure=TimeDuration(1.0, TimeUnit.HOURS),
            ),
            "FM-2": Faalwijze(
                fm_id="FM-2",
                pbs_id="PBS-1",
                functie_id="F",
                faalwijze_omschrijving="Duur",
                mttf_jaar=10.0,
                is_evident=True,
                downtime_per_failure=TimeDuration(1.0, TimeUnit.HOURS),
            ),
        },
    )
    fmrs = [
        FMResult(
            fm_id="FM-1",
            pbs_id="PBS-1",
            p_failure_lifecycle=0.1,
            expected_failures=1.0,
            expected_raw_downtime_hr=1.0,
            expected_detection_delay_hr=0.0,
            expected_total_downtime_hr=1.0,
            expected_pm_downtime_hr=0.0,
            expected_cm_cost_eur=0.0,
            pm_cost_eur=0.0,
            total_cost_eur=50.0,
            risk_contribution=0.0,
            horizon_profile=FMHorizonProfile(
                cor_eur=[0.0] * 5,
                cor_downtime_hr=[0.0] * 5,
                hidden_nb_hr=[0.0] * 5,
            ),
        ),
        FMResult(
            fm_id="FM-2",
            pbs_id="PBS-1",
            p_failure_lifecycle=0.1,
            expected_failures=1.0,
            expected_raw_downtime_hr=1.0,
            expected_detection_delay_hr=0.0,
            expected_total_downtime_hr=1.0,
            expected_pm_downtime_hr=0.0,
            expected_cm_cost_eur=0.0,
            pm_cost_eur=0.0,
            total_cost_eur=200.0,
            risk_contribution=0.0,
            horizon_profile=FMHorizonProfile(
                cor_eur=[0.0] * 5,
                cor_downtime_hr=[0.0] * 5,
                hidden_nb_hr=[0.0] * 5,
            ),
        ),
    ]
    window._state.set_last_project(project)
    window._state.set_last_run(build_run_result(project, fmrs))
    app.processEvents()
    switch_workspace_modus(window, "fm_detail", app)
    window.workspace_state.set_contribution_presentation(
        ContributionPresentation(horizon="lifecycle")
    )
    app.processEvents()

    model = window.fm_table_view.model()
    assert model.rowCount() == 2
    _set_text_filter(window, FM_COL_KOSTEN, ">100")
    app.processEvents()
    assert model.rowCount() == 1
    assert model.data(model.index(0, 0), RAW_ROLE) == "FM-2"


def test_clear_button_restores_all_rows(monkeypatch) -> None:
    app, window = _window_in_fm_detail(monkeypatch)
    model = window.fm_table_view.model()
    total = model.rowCount()
    _set_text_filter(window, FM_COL_BOUWDEEL, "zzz_geen_match")
    _set_bool_filter(window, FM_COL_NMF, True)
    app.processEvents()
    assert model.rowCount() == 0
    window.fm_filter_clear_button.click()
    app.processEvents()
    assert model.rowCount() == total
    assert window.fm_table_filter_row.text_value(FM_COL_BOUWDEEL) == ""
    assert window.fm_table_filter_row.bool_value(FM_COL_NMF) is None


def test_row_count_updates_with_filter(monkeypatch) -> None:
    app, window = _window_in_fm_detail(monkeypatch)
    total = window.fm_table_view.model().rowCount()
    assert window.fm_filter_row_count_label.text() == f"{total} / {total} rijen"
    _set_text_filter(window, FM_COL_BOUWDEEL, "zzz_geen_match")
    app.processEvents()
    assert window.fm_filter_row_count_label.text() == f"0 / {total} rijen"


def test_invalid_numeric_shows_all_rows_with_error_style(monkeypatch) -> None:
    app, window = _window_in_fm_detail(monkeypatch)
    model = window.fm_table_view.model()
    total = model.rowCount()
    _set_text_filter(window, FM_COL_KOSTEN, ">>bad")
    app.processEvents()
    assert model.rowCount() == total
    editor = window.fm_table_filter_row.editor(FM_COL_KOSTEN)
    assert isinstance(editor, QLineEdit)
    assert "E65100" in editor.styleSheet()


def test_filters_empty_after_window_restart(monkeypatch) -> None:
    app, window = _window_in_fm_detail(monkeypatch)
    _set_text_filter(window, FM_COL_BOUWDEEL, "pomp")
    _set_text_filter(window, FM_COL_KOSTEN, ">10")
    app.processEvents()
    assert window.fm_table_filter_row.text_value(FM_COL_BOUWDEEL) == "pomp"

    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    window.close()
    app.processEvents()
    fresh = ResultsWorkspaceWindow()
    fresh.show()
    app.processEvents()
    assert fresh.fm_table_filter_row.text_value(FM_COL_BOUWDEEL) == ""
    assert fresh.fm_table_filter_row.numeric_value(FM_COL_KOSTEN) == ""
