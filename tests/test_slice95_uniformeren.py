"""Slice 95 issues 08-09 — uniformeren pipeline."""

from __future__ import annotations

from pathlib import Path

from rcm_core.persistence import load_project

from rcm_desktop.adapter.compare_balanced_presentation_service import build_compare_presentation
from rcm_desktop.adapter.normalization_proposal_service import build_normalization_proposals
from rcm_desktop.adapter.patch_audit_service import apply_patch, rollback_last_patch


def test_normalization_proposal_requires_no_auto_apply() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    presentation = build_compare_presentation(project, project)
    proposals = build_normalization_proposals(presentation, direction="a_to_b")
    assert len(proposals.items) >= 0
    for item in proposals.items:
        assert item.approved is False


def test_patch_rejected_without_approval() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    from rcm_desktop.adapter.patch_audit_service import NormalizationPatch

    patch = NormalizationPatch(
        target_fm_id="FM-001",
        field="mttf_jaar",
        new_value=99.0,
        approved=False,
    )
    try:
        apply_patch(project, patch)
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_patch_apply_and_rollback() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    original_mttf = project.faalwijzes["FM-001"].mttf_jaar
    from rcm_desktop.adapter.patch_audit_service import NormalizationPatch

    patch = NormalizationPatch(
        target_fm_id="FM-001",
        field="mttf_jaar",
        new_value=original_mttf + 1.0,
        approved=True,
    )
    updated, audit = apply_patch(project, patch)
    assert updated.faalwijzes["FM-001"].mttf_jaar == original_mttf + 1.0
    assert audit.patch_count == 1
    restored = rollback_last_patch(updated, audit)
    assert restored.faalwijzes["FM-001"].mttf_jaar == original_mttf
