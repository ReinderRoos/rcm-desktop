"""Slice 59.2–59.5 — FM-editor lifecycle, resultaten-tab (pytest-qt smoke)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_core.incremental_run import IncrementalRunResult
from rcm_core.models import FMResult
from rcm_core.persistence import load_project
from rcm_desktop import messages
from rcm_desktop.adapter.fm_edit_commit_service import (
    FmEditCommitResult,
    create_edit_session,
    insert_fm_scope,
)
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.fm_edit_scope_loader import load_fm_edit_scope, seed_create_bundle
from rcm_desktop.views.fm_editor_dialog import FmEditorDialog


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


@pytest.fixture
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()


def test_fm_editor_has_save_lifecycle_buttons(sample_project, qt_app) -> None:
    _ = qt_app
    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-001")
    assert dialog._save_btn.text() == messages.FM_EDITOR_SAVE
    assert dialog._save_close_btn.text() == messages.FM_EDITOR_SAVE_AND_CLOSE
    assert dialog._cancel_btn.text() == "Annuleren"
    dialog.close()


def test_fm_editor_results_tab_empty_before_run(sample_project, qt_app) -> None:
    _ = qt_app
    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-001")
    assert messages.FM_EDITOR_RESULTS_EMPTY in dialog._results_summary.text()
    dialog.close()


def test_fm_editor_save_stays_open_clears_dirty(
    sample_project, qt_app, monkeypatch
) -> None:
    _ = qt_app
    session = create_edit_session(sample_project)
    dialog = FmEditorDialog(
        None,
        project=sample_project,
        fm_id="FM-001",
        editing_session=session,
    )
    dialog._omschrijving.setText("Gewijzigd scenario")
    dialog._dirty = True
    dialog._mttf.setValue(42.0)

    mock_result = FmEditCommitResult(
        ok=True,
        errors=(),
        affected_fm_ids=("FM-001",),
        project=sample_project,
        run_result=RunResult(
            status="done",
            summary="ok",
            metrics=RunMetrics(
                fm_result_count=1,
                total_lifecycle_faalmomenten=2.5,
                total_cost_eur=1000.0,
                total_downtime_hr=12.0,
                lifecycle_years=float(sample_project.config.lifecycle_years),
                total_risk_contribution=0.1,
            ),
            fm_core_results=(),
            rows=(),
        ),
    )
    monkeypatch.setattr(
        "rcm_desktop.views.fm_editor_dialog.commit_fm_edit",
        lambda *_a, **_k: mock_result,
    )

    dialog._commit(stay_open=True)
    assert dialog._dirty is False
    dialog.close()


def test_fm_editor_results_tab_after_commit(
    sample_project, qt_app, monkeypatch
) -> None:
    _ = qt_app
    fmr = FMResult(
        fm_id="FM-001",
        pbs_id="PBS-001-1",
        p_failure_lifecycle=0.5,
        expected_failures=2.5,
        expected_raw_downtime_hr=8.0,
        expected_detection_delay_hr=1.0,
        expected_total_downtime_hr=12.0,
        expected_pm_downtime_hr=3.0,
        expected_cm_cost_eur=800.0,
        pm_cost_eur=200.0,
        total_cost_eur=1000.0,
        risk_contribution=0.1,
    )
    mock_result = FmEditCommitResult(
        ok=True,
        errors=(),
        affected_fm_ids=("FM-001",),
        project=sample_project,
        run_result=RunResult(
            status="done",
            summary="ok",
            metrics=RunMetrics(
                fm_result_count=1,
                total_lifecycle_faalmomenten=2.5,
                total_cost_eur=1000.0,
                total_downtime_hr=12.0,
                lifecycle_years=float(sample_project.config.lifecycle_years),
                total_risk_contribution=0.1,
            ),
            fm_core_results=(fmr,),
            rows=(),
        ),
    )
    monkeypatch.setattr(
        "rcm_desktop.views.fm_editor_dialog.commit_fm_edit",
        lambda *_a, **_k: mock_result,
    )

    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-001")
    dialog._omschrijving.setText("Scenario met resultaten")
    dialog._commit(stay_open=True)
    assert "2.50" in dialog._results_summary.text()
    dialog.close()


def test_fm_editor_create_mode_exits_after_first_save(
    sample_project, qt_app, monkeypatch
) -> None:
    _ = qt_app
    session = create_edit_session(sample_project)
    dialog = FmEditorDialog(
        None,
        project=sample_project,
        create_pbs_id="PBS-001-1",
        editing_session=session,
    )
    assert dialog._create_mode is True
    dialog._omschrijving.setText("Nieuwe faalwijze test")
    dialog._mttf.setValue(12.0)

    mock_inc = MagicMock(
        return_value=IncrementalRunResult(
            fm_results={},
            pbs_results={},
            cache_only=False,
            affected_fm_ids=[dialog._fm_id],
            recalculated_fm_count=1,
        )
    )
    monkeypatch.setattr(
        "rcm_desktop.adapter.fm_edit_commit_service.run_incremental_analysis",
        mock_inc,
    )

    dialog._commit(stay_open=True)
    assert dialog._create_mode is False
    bundle = load_fm_edit_scope(session, dialog._fm_id)
    assert bundle.faalwijze_row["faalwijze_omschrijving"] == "Nieuwe faalwijze test"
    dialog.close()


def test_insert_fm_scope_adds_new_fm(sample_project) -> None:
    session = create_edit_session(sample_project)
    bundle = seed_create_bundle(session, "PBS-001-1")
    row = dict(bundle.faalwijze_row)
    row["faalwijze_omschrijving"] = "Via insert_fm_scope"
    bundle = type(bundle)(
        fm_id=bundle.fm_id,
        faalwijze_row=row,
        pbs_row=bundle.pbs_row,
        fm_effect_rows=bundle.fm_effect_rows,
        pm_task_rows=bundle.pm_task_rows,
        pm_effect_rows=bundle.pm_effect_rows,
        task_group_rows=bundle.task_group_rows,
        effect_klasse_rows=bundle.effect_klasse_rows,
    )
    insert_fm_scope(session, bundle)
    ids = {str(r.get("fm_id")) for r in session.session["edit_current"]["faalwijzes"]}
    assert bundle.fm_id in ids
