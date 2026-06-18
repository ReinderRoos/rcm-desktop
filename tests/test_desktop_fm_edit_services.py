from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rcm_core.persistence import load_project
from rcm_core.editing.validation import normalize_key
from rcm_desktop.adapter.fm_edit_bundle_service import (
    count_faalwijzen_for_pbs,
    count_faalwijzen_for_pbs_in_edit,
    count_faalwijzen_for_task_group,
    count_faalwijzen_for_task_group_in_edit,
    load_bundle,
)
from rcm_desktop.adapter.fm_edit_scope_loader import load_fm_edit_scope
from rcm_desktop.adapter.fm_edit_commit_facade import commit_fm_edit
from rcm_desktop.adapter.fm_edit_bundle_assembler import FmEditDraft, assemble_bundle
from rcm_desktop.adapter.fm_edit_commit_service import (
    apply_bundle_scope,
    commit_edits,
    create_edit_session,
)
from rcm_desktop.adapter.fm_edit_row_mappers import downtime_dict_from_hours, downtime_hours_from_row
from rcm_desktop.adapter.fm_edit_bundle_service import load_bundle_from_session
from rcm_core.incremental_run import IncrementalRunResult


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def test_load_fm_edit_scope_project_matches_session(sample_project) -> None:
    session = create_edit_session(sample_project)
    from_project = load_fm_edit_scope(sample_project, "FM-001")
    from_session = load_fm_edit_scope(session, "FM-001")
    assert from_project.fm_id == from_session.fm_id
    assert from_project.faalwijze_row == from_session.faalwijze_row
    assert from_project.pbs_row == from_session.pbs_row
    assert from_project.fm_effect_rows == from_session.fm_effect_rows
    assert from_project.pm_task_rows == from_session.pm_task_rows


def test_load_bundle_scope_for_fm001(sample_project) -> None:
    bundle = load_bundle(sample_project, "FM-001")
    assert bundle.fm_id == "FM-001"
    assert bundle.faalwijze_row["fm_id"] == "FM-001"
    assert bundle.pbs_row["pbs_id"] == bundle.faalwijze_row["pbs_id"]
    assert len(bundle.fm_effect_rows) == 2
    assert all(r["fm_id"] == "FM-001" for r in bundle.fm_effect_rows)
    pm_ids = {r["pm_id"] for r in bundle.pm_task_rows}
    for link in bundle.pm_effect_rows:
        assert link["pm_id"] in pm_ids


def test_commit_fm_edit_applies_bundle_and_runs(sample_project, tmp_path, monkeypatch) -> None:
    path = tmp_path / "proj.rcm.json"
    path.write_text(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))

    session = create_edit_session(sample_project)
    bundle = load_fm_edit_scope(sample_project, "FM-001")
    row = dict(bundle.faalwijze_row)
    row["mttf_jaar"] = 22.0
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

    mock_inc = MagicMock(
        return_value=IncrementalRunResult(
            fm_results={},
            pbs_results={},
            cache_only=False,
            affected_fm_ids=["FM-001"],
            recalculated_fm_count=1,
        )
    )
    monkeypatch.setattr(
        "rcm_desktop.adapter.fm_edit_commit_service.run_incremental_analysis",
        mock_inc,
    )

    result = commit_fm_edit(session, bundle, path=path, save_to_disk=False)
    assert result.ok is True
    assert result.project is not None
    assert result.project.faalwijzes["FM-001"].mttf_jaar == pytest.approx(22.0)
    mock_inc.assert_called_once()
    assert mock_inc.call_args.kwargs.get("full_recompute") is False


def test_commit_fm_edit_validation_error(sample_project) -> None:
    session = create_edit_session(sample_project)
    bundle = load_fm_edit_scope(sample_project, "FM-001")
    row = dict(bundle.faalwijze_row)
    row["mttf_jaar"] = 0.0
    bad = type(bundle)(
        fm_id=bundle.fm_id,
        faalwijze_row=row,
        pbs_row=bundle.pbs_row,
        fm_effect_rows=bundle.fm_effect_rows,
        pm_task_rows=bundle.pm_task_rows,
        pm_effect_rows=bundle.pm_effect_rows,
        task_group_rows=bundle.task_group_rows,
        effect_klasse_rows=bundle.effect_klasse_rows,
    )
    result = commit_fm_edit(session, bad, path=None, save_to_disk=False)
    assert result.ok is False
    assert result.errors
    assert result.project is None


def test_commit_mttf_change_triggers_incremental_run(sample_project, tmp_path, monkeypatch) -> None:
    path = tmp_path / "proj.rcm.json"
    path.write_text(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))

    session = create_edit_session(sample_project)
    bundle = load_bundle(sample_project, "FM-001")
    row = dict(bundle.faalwijze_row)
    row["mttf_jaar"] = 22.0
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
    apply_bundle_scope(session, bundle)

    mock_inc = MagicMock(
        return_value=IncrementalRunResult(
            fm_results={},
            pbs_results={},
            cache_only=False,
            affected_fm_ids=["FM-001"],
            recalculated_fm_count=1,
        )
    )
    monkeypatch.setattr(
        "rcm_desktop.adapter.fm_edit_commit_service.run_incremental_analysis",
        mock_inc,
    )

    result = commit_edits(session, project_path=path, save_to_disk=False)
    assert result.ok is True
    assert result.project is not None
    assert result.project.faalwijzes["FM-001"].mttf_jaar == pytest.approx(22.0)
    mock_inc.assert_called_once()
    assert mock_inc.call_args.kwargs.get("full_recompute") is False


def test_count_pbs_in_edit_matches_project_baseline(sample_project) -> None:
    session = create_edit_session(sample_project)
    pbs_id = "PBS-001-1"
    assert count_faalwijzen_for_pbs_in_edit(session, pbs_id) == count_faalwijzen_for_pbs(
        sample_project, pbs_id
    )
    assert count_faalwijzen_for_pbs_in_edit(session, pbs_id) >= 2


def test_count_pbs_in_edit_drops_when_fm_row_removed_from_session(sample_project) -> None:
    session = create_edit_session(sample_project)
    pbs_id = "PBS-001-1"
    before = count_faalwijzen_for_pbs_in_edit(session, pbs_id)
    rows = [
        r
        for r in session.session["edit_current"]["faalwijzes"]
        if normalize_key(r.get("fm_id")) != "FM-001"
    ]
    session.apply_entity_rows("faalwijzes", rows)
    after = count_faalwijzen_for_pbs_in_edit(session, pbs_id)
    assert after == before - 1


def test_count_task_group_in_edit_matches_project_baseline(sample_project) -> None:
    session = create_edit_session(sample_project)
    group_id = "TG-001"
    assert count_faalwijzen_for_task_group_in_edit(
        session, group_id
    ) == count_faalwijzen_for_task_group(sample_project, group_id)
    assert count_faalwijzen_for_task_group_in_edit(session, group_id) >= 2


def test_replace_fm_scope_matches_apply_bundle_scope(sample_project) -> None:
    session_apply = create_edit_session(sample_project)
    session_replace = create_edit_session(sample_project)
    bundle = load_bundle(sample_project, "FM-001")
    row = dict(bundle.faalwijze_row)
    row["mttf_jaar"] = 33.0
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
    apply_bundle_scope(session_apply, bundle)
    from rcm_desktop.adapter.fm_edit_commit_service import replace_fm_scope

    replace_fm_scope(session_replace, bundle)
    assert (
        session_apply.session["edit_current"]["faalwijzes"]
        == session_replace.session["edit_current"]["faalwijzes"]
    )


def test_downtime_mapper_round_trip() -> None:
    d = downtime_dict_from_hours(4.5)
    row = {"downtime_per_failure": d}
    assert downtime_hours_from_row(row) == pytest.approx(4.5)


def test_assembler_round_trip(sample_project) -> None:
    baseline = load_bundle(sample_project, "FM-001")
    draft = FmEditDraft(
        fm_id="FM-001",
        baseline=baseline,
        failure_type="aging",
        mttf_jaar=12.0,
        sigma_jaar=2.0,
        is_evident=True,
        faalwijze_omschrijving="Asm test",
        functie_id="FUNC-001",
        repair_quality=0.5,
        cm_materiaal=100.0,
        cm_arbeid=50.0,
        downtime_hours=3.0,
        notes="n",
        aanname_cm_kosten="",
        aanname_downtime="",
        bouwjaar=2000,
        fm_effect_rows=baseline.fm_effect_rows,
        pm_task_rows=baseline.pm_task_rows,
        pm_effect_rows=baseline.pm_effect_rows,
        effect_klasse_rows=baseline.effect_klasse_rows,
        task_group_rows=baseline.task_group_rows,
    )
    built = assemble_bundle(draft)
    assert built.faalwijze_row["failure_type"] == "aging"
    assert built.faalwijze_row["mttf_jaar"] == pytest.approx(12.0)
    assert built.faalwijze_row["downtime_per_failure"]["value"] == pytest.approx(3.0)


def test_load_bundle_from_session_after_grid_edit(sample_project) -> None:
    from rcm_desktop.adapter.entity_edit_service import EntityEditService

    grid = EntityEditService.for_view("input.faalwijzen")
    grid.init(sample_project)
    grid.apply_change("FM-001", "failure_type", "random")
    bundle = load_bundle_from_session(grid.editing_session, "FM-001")
    assert bundle.faalwijze_row["failure_type"] == "random"


def test_commit_blocked_on_validation_error(sample_project) -> None:
    session = create_edit_session(sample_project)
    bundle = load_bundle(sample_project, "FM-001")
    row = dict(bundle.faalwijze_row)
    row["mttf_jaar"] = 0.0
    bad = type(bundle)(
        fm_id=bundle.fm_id,
        faalwijze_row=row,
        pbs_row=bundle.pbs_row,
        fm_effect_rows=bundle.fm_effect_rows,
        pm_task_rows=bundle.pm_task_rows,
        pm_effect_rows=bundle.pm_effect_rows,
        task_group_rows=bundle.task_group_rows,
        effect_klasse_rows=bundle.effect_klasse_rows,
    )
    apply_bundle_scope(session, bad)
    result = commit_edits(session, project_path=None, save_to_disk=False)
    assert result.ok is False
    assert result.errors
    assert result.project is None
