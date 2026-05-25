from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rcm_core.persistence import load_project
from rcm_desktop.adapter.fm_edit_bundle_service import load_bundle
from rcm_desktop.adapter.fm_edit_commit_service import (
    apply_bundle_scope,
    commit_edits,
    create_edit_session,
)
from rcm_core.incremental_run import IncrementalRunResult


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


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
