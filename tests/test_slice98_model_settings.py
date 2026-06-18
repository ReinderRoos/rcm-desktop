"""Slice 98 issue 07 — modelinstellingen MC N/seed."""

from __future__ import annotations

from rcm_core.config import RCMConfig
from rcm_core.models import RCMProject
from rcm_desktop.adapter.isograph_import_service import build_from_sheets
from rcm_desktop.adapter.model_settings_service import (
    apply_draft_to_project,
    build_draft,
    commit_model_settings,
    compute_requires_rerun,
    validate_draft,
)


def _project(**kw) -> RCMProject:
    return RCMProject(config=RCMConfig(lifecycle_years=80.0, modeljaar=2026, **kw))


def test_mc_n_change_requires_rerun():
    project = _project(monte_carlo_n=10_000)
    baseline = build_draft(project)
    draft = type(baseline)(**{**baseline.__dict__, "monte_carlo_n": 5000})
    assert compute_requires_rerun(baseline, draft)


def test_mc_seed_change_requires_rerun():
    project = _project(monte_carlo_seed=None)
    baseline = build_draft(project)
    draft = type(baseline)(**{**baseline.__dict__, "monte_carlo_seed": 42})
    assert compute_requires_rerun(baseline, draft)


def test_validate_draft_blocks_mc_n_below_100():
    project = _project()
    baseline = build_draft(project)
    draft = type(baseline)(**{**baseline.__dict__, "monte_carlo_n": 50})
    errors = validate_draft(draft)
    assert any("100" in e for e in errors)


def test_apply_draft_persists_mc_fields():
    project = _project(monte_carlo_n=10_000, monte_carlo_seed=None)
    baseline = build_draft(project)
    draft = type(baseline)(**{**baseline.__dict__, "monte_carlo_n": 2500, "monte_carlo_seed": 99})
    updated = apply_draft_to_project(project, draft)
    assert updated.config.monte_carlo_n == 2500
    assert updated.config.monte_carlo_seed == 99


def test_commit_mc_settings_ok(tmp_path):
    project = _project()
    baseline = build_draft(project)
    draft = type(baseline)(**{**baseline.__dict__, "monte_carlo_n": 1000, "monte_carlo_seed": 7})
    path = tmp_path / "proj.rcm.json"
    from rcm_core.persistence import save_project

    save_project(project, path)
    result = commit_model_settings(project, draft, baseline=baseline, project_path=path)
    assert result.ok
    assert result.requires_rerun
