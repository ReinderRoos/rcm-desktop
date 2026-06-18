"""Slice 59.1 — FM create workflow (TDD)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.persistence import load_project


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def test_allocate_fm_id_skips_existing_ids(sample_project) -> None:
    from rcm_desktop.adapter.fm_create_service import allocate_fm_id

    assert allocate_fm_id(sample_project) == "FM-007"


def test_default_functie_id_uses_first_sibling_on_pbs(sample_project) -> None:
    from rcm_desktop.adapter.fm_create_service import default_functie_id_for_pbs

    assert default_functie_id_for_pbs(sample_project, "PBS-001-1") == "FUNC-001"


def test_seed_create_bundle_allocates_new_fm_on_pbs(sample_project) -> None:
    from rcm_desktop.adapter.fm_edit_commit_service import create_edit_session
    from rcm_desktop.adapter.fm_edit_scope_loader import seed_create_bundle

    session = create_edit_session(sample_project)
    bundle = seed_create_bundle(session, "PBS-001-1")
    assert bundle.fm_id == "FM-007"
    assert bundle.faalwijze_row["pbs_id"] == "PBS-001-1"
    assert bundle.faalwijze_row["functie_id"] == "FUNC-001"
    assert bundle.fm_effect_rows == ()
    assert bundle.pm_task_rows == ()


def test_commit_new_fm_inserts_and_runs(sample_project, tmp_path, monkeypatch) -> None:
    from unittest.mock import MagicMock

    from rcm_core.incremental_run import IncrementalRunResult
    from rcm_desktop.adapter.fm_edit_bundle_assembler import FmEditDraft, assemble_bundle
    from rcm_desktop.adapter.fm_edit_commit_facade import commit_fm_edit
    from rcm_desktop.adapter.fm_edit_commit_service import create_edit_session
    from rcm_desktop.adapter.fm_edit_scope_loader import seed_create_bundle

    path = tmp_path / "proj.rcm.json"
    path.write_text(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))

    session = create_edit_session(sample_project)
    bundle = seed_create_bundle(session, "PBS-001-1")
    row = dict(bundle.faalwijze_row)
    row["faalwijze_omschrijving"] = "Nieuwe test faalwijze"
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
    draft = FmEditDraft(
        fm_id=bundle.fm_id,
        baseline=bundle,
        failure_type=row["failure_type"],
        aging_distribution=row["aging_distribution"],
        mttf_jaar=row["mttf_jaar"],
        sigma_jaar=row["sigma_jaar"],
        beta_jaar=row["beta_jaar"],
        is_evident=row["is_evident"],
        faalwijze_omschrijving=row["faalwijze_omschrijving"],
        functie_id=row["functie_id"],
        repair_quality=row["repair_quality"],
        cm_materiaal=0.0,
        cm_arbeid=0.0,
        downtime_hours=0.0,
        notes="",
        aanname_cm_kosten="",
        aanname_downtime="",
        bouwjaar=bundle.pbs_row.get("bouwjaar") or 0,
        fm_effect_rows=(),
        pm_task_rows=(),
        pm_effect_rows=(),
        effect_klasse_rows=(),
        task_group_rows=(),
    )
    bundle = assemble_bundle(draft)

    mock_inc = MagicMock(
        return_value=IncrementalRunResult(
            fm_results={},
            pbs_results={},
            cache_only=False,
            affected_fm_ids=["FM-007"],
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
    assert "FM-007" in result.project.faalwijzes
    assert result.project.faalwijzes["FM-007"].faalwijze_omschrijving == "Nieuwe test faalwijze"
    assert "FM-007" in result.affected_fm_ids
