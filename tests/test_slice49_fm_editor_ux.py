"""Slice 49 — FM-editor UX & modelwaarschuwingen."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.editing.validation import validate_entity_rows
from rcm_core.persistence import load_project
from rcm_desktop.adapter.fk_normalization import normalize_optional_fk
from rcm_desktop.adapter.fm_edit_consistency import (
    count_cross_component_peers,
    findings_for_edit_rows,
    findings_for_fm_from_project,
    intervals_within_ten_percent,
    normalize_pm_omschrijving,
)
from rcm_desktop.adapter.fm_edit_commit_service import create_edit_session
from rcm_desktop.adapter.fm_sigma_coupling import coupled_sigma, is_sigma_manual
from rcm_desktop.adapter.results_workspace_state import MODE_BIJDRAGEN, MODE_FM_DETAIL
from rcm_desktop.app_state import AppState


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def test_normalize_optional_fk_maps_none_strings_to_none() -> None:
    assert normalize_optional_fk(None) is None
    assert normalize_optional_fk("") is None
    assert normalize_optional_fk("None") is None
    assert normalize_optional_fk("null") is None
    assert normalize_optional_fk("TG-001") == "TG-001"


def test_validate_pm_tasks_skips_none_string_task_group_fk(sample_project) -> None:
    session = create_edit_session(sample_project)
    edit_current = session.session["edit_current"]
    rows = [dict(r) for r in edit_current["pm_tasks"]]
    rows[0] = dict(rows[0])
    rows[0]["task_group_id"] = "None"
    coerced, errors = validate_entity_rows(
        "pm_tasks", rows, sample_project, edit_current
    )
    assert not errors
    assert coerced[0]["task_group_id"] in ("None", None, "")


def test_coupled_sigma_is_fifteen_percent() -> None:
    assert coupled_sigma(100.0) == pytest.approx(15.0)


def test_is_sigma_manual_when_deviating_from_fifteen_percent() -> None:
    assert is_sigma_manual(100.0, 15.0) is False
    assert is_sigma_manual(100.0, 20.0) is True


def test_app_state_preserve_workspace_ui_flag() -> None:
    state = AppState()
    state.set_last_project(None, preserve_workspace_ui=True)
    assert state.take_preserve_workspace_ui() is True
    assert state.take_preserve_workspace_ui() is False


def test_findings_aging_without_rev(sample_project) -> None:
    session = create_edit_session(sample_project)
    current = session.session["edit_current"]
    faal = [dict(r) for r in current["faalwijzes"]]
    pm = [dict(r) for r in current["pm_tasks"]]
    for row in faal:
        if row["fm_id"] == "FM-001":
            row["failure_type"] = "aging"
    pm = [r for r in pm if not (r["fm_id"] == "FM-001" and r.get("taak_type") == "REV")]
    findings = findings_for_edit_rows("FM-001", faal, pm)
    codes = {f.code for f in findings}
    assert "AGING_WITHOUT_REV" in codes


def test_findings_rev_without_aging(sample_project) -> None:
    session = create_edit_session(sample_project)
    current = session.session["edit_current"]
    faal = [dict(r) for r in current["faalwijzes"]]
    pm = [dict(r) for r in current["pm_tasks"]]
    for row in faal:
        if row["fm_id"] == "FM-002":
            row["failure_type"] = "random"
    findings = findings_for_edit_rows("FM-002", faal, pm)
    codes = {f.code for f in findings}
    assert "REV_WITHOUT_AGING" not in codes
    pm.append(
        {
            "pm_id": "PM-X",
            "fm_id": "FM-002",
            "taak_type": "REV",
            "taak_omschrijving": "Test REV",
            "interval_jaar": 5.0,
            "task_group_id": None,
        }
    )
    findings = findings_for_edit_rows("FM-002", faal, pm)
    assert any(f.code == "REV_WITHOUT_AGING" for f in findings)


def test_cross_component_pm_bundle_suggest() -> None:
    faal = [
        {"fm_id": "FM-A", "pbs_id": "PBS-1", "failure_type": "random"},
        {"fm_id": "FM-B", "pbs_id": "PBS-2", "failure_type": "random"},
    ]
    pm = [
        {
            "pm_id": "PM-A1",
            "fm_id": "FM-A",
            "taak_type": "IN",
            "taak_omschrijving": "Inspectieronde",
            "interval_jaar": 1.0,
            "task_group_id": None,
        },
        {
            "pm_id": "PM-B1",
            "fm_id": "FM-B",
            "taak_type": "IN",
            "taak_omschrijving": "Inspectieronde",
            "interval_jaar": 1.0,
            "task_group_id": None,
        },
    ]
    peers = count_cross_component_peers(
        pm[0],
        fm_id="FM-A",
        pbs_id="PBS-1",
        pm_rows=pm,
        fm_pbs_by_id={"FM-A": "PBS-1", "FM-B": "PBS-2"},
    )
    assert peers == 1
    findings = findings_for_edit_rows("FM-A", faal, pm)
    assert any(f.code == "PM_BUNDLE_SUGGEST" and f.peer_count == 1 for f in findings)


def test_cross_component_skips_rev_and_same_pbs() -> None:
    pm = {
        "pm_id": "PM-R",
        "fm_id": "FM-A",
        "taak_type": "REV",
        "taak_omschrijving": "Revisie",
        "interval_jaar": 5.0,
        "task_group_id": None,
    }
    assert (
        count_cross_component_peers(
            pm,
            fm_id="FM-A",
            pbs_id="PBS-1",
            pm_rows=[pm],
            fm_pbs_by_id={"FM-A": "PBS-1", "FM-B": "PBS-2"},
        )
        == 0
    )


def test_intervals_within_ten_percent() -> None:
    assert intervals_within_ten_percent(1.0, 1.05) is True
    assert intervals_within_ten_percent(1.0, 1.2) is False


def test_normalize_pm_omschrijving() -> None:
    assert normalize_pm_omschrijving("  Inspectie  RONDE ") == "inspectie ronde"


def test_fm001_baseline_has_no_aging_without_rev(sample_project) -> None:
    findings = findings_for_fm_from_project(sample_project, "FM-001")
    assert not any(f.code == "AGING_WITHOUT_REV" for f in findings)


def test_workspace_state_reset_after_preserve_consumed(sample_project) -> None:
    from rcm_desktop.adapter.results_workspace_state import ResultsWorkspaceState

    app = AppState()
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_FM_DETAIL)
    app.set_last_project(sample_project, preserve_workspace_ui=True)
    preserve = app.take_preserve_workspace_ui()
    assert preserve is True
    if not preserve:
        ws.reset_for_new_project()
    assert ws.snapshot().modus == MODE_FM_DETAIL
    ws.reset_for_new_project()
    assert ws.snapshot().modus == MODE_BIJDRAGEN
