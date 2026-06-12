"""Slice 59 — field copy, taakgroep, resultaten (TDD)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.models import FMResult
from rcm_core.persistence import load_project
from rcm_desktop.adapter.fm_edit_commit_service import create_edit_session
from rcm_desktop.adapter.fm_field_copy_service import copy_fields
from rcm_desktop.adapter.fm_editor_results_view_service import build_editor_results_view
from rcm_desktop.adapter.pm_measure_link_service import apply_task_group_link
from rcm_desktop.adapter.task_group_catalog_service import fms_for_group, list_task_groups


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def test_copy_fields_preserves_target_ids(sample_project) -> None:
    source = sample_project.faalwijzes["FM-001"].to_dict()
    target = sample_project.faalwijzes["FM-002"].to_dict()
    copied = copy_fields(source, target)
    assert copied["fm_id"] == "FM-002"
    assert copied["pbs_id"] == target["pbs_id"]
    assert "pm_id" not in copied or copied.get("fm_id") != source["fm_id"]


def test_fms_for_group_returns_sorted_fm_ids(sample_project) -> None:
    session = create_edit_session(sample_project)
    fm_ids = fms_for_group(session, "TG-001")
    assert "FM-002" in fm_ids
    assert fm_ids == tuple(sorted(fm_ids))


def test_copy_fields_basis_and_correctief_only(sample_project) -> None:
    source = sample_project.faalwijzes["FM-001"].to_dict()
    target = sample_project.faalwijzes["FM-002"].to_dict()
    before_pm_id = target["fm_id"]
    copied = copy_fields(source, target)
    assert copied["fm_id"] == before_pm_id
    assert copied["pbs_id"] == target["pbs_id"]
    assert copied["mttf_jaar"] == source["mttf_jaar"]
    assert copied["cost_cm_eur"] == source["cost_cm_eur"]


def test_list_task_groups_includes_shared_fm_ids(sample_project) -> None:
    session = create_edit_session(sample_project)
    groups = list_task_groups(session)
    tg001 = next(g for g in groups if g.group_id == "TG-001")
    assert "FM-002" in tg001.fm_ids
    assert len(tg001.fm_ids) >= 2


def test_apply_task_group_link_inherits_interval(sample_project) -> None:
    session = create_edit_session(sample_project)
    pm_row = {"pm_id": "PM-NEW", "fm_id": "FM-007", "interval_jaar": 1.0, "cost_eur": 0.0}
    linked = apply_task_group_link(pm_row, "TG-001", session)
    assert linked["task_group_id"] == "TG-001"
    assert linked["interval_jaar"] == pytest.approx(1.0)
    assert linked["cost_eur"] == pytest.approx(500.0)


def test_build_editor_results_view_without_run(sample_project) -> None:
    view = build_editor_results_view(sample_project, "FM-001", None)
    assert view.has_results is False
    assert view.pm_rows


def test_build_editor_results_view_with_fmr(sample_project) -> None:
    fmr = FMResult(
        fm_id="FM-001",
        pbs_id="PBS-001-1",
        p_failure_lifecycle=0.5,
        expected_failures=3.0,
        expected_raw_downtime_hr=10.0,
        expected_detection_delay_hr=1.0,
        expected_total_downtime_hr=20.0,
        expected_pm_downtime_hr=5.0,
        expected_cm_cost_eur=1000.0,
        pm_cost_eur=500.0,
        total_cost_eur=1500.0,
        risk_contribution=0.1,
    )
    view = build_editor_results_view(sample_project, "FM-001", fmr)
    assert view.has_results is True
    assert view.expected_failures == pytest.approx(3.0)
    assert view.total_downtime_hr == pytest.approx(20.0)
