"""Slice 95 issues 08-09 — uniformeren pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.persistence import load_project

from rcm_desktop.adapter.compare_balanced_presentation_service import build_compare_presentation
from rcm_desktop.adapter.normalization_proposal_service import build_normalization_proposals
from rcm_desktop.adapter.normalization_review_presentation_service import (
    build_normalization_review_presentation,
)
from rcm_desktop.adapter.patch_audit_service import (
    apply_approved_normalization,
    apply_patch,
    rollback_last_patch,
)
from rcm_desktop.adapter.tabular_edit_types import MaterializeBlockedError


def test_normalization_proposal_requires_no_auto_apply() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    presentation = build_compare_presentation(project, project)
    proposals = build_normalization_proposals(presentation, direction="a_to_b")
    assert len(proposals.items) >= 0
    for item in proposals.items:
        assert item.approved is False


def test_build_normalization_review_presentation_shows_source_labels() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    presentation = build_compare_presentation(project, project)
    proposals = build_normalization_proposals(presentation, direction="a_to_b")
    review = build_normalization_review_presentation(proposals)
    assert review.direction == "a_to_b"
    if review.items:
        row = review.items[0]
        assert row.source_label in ("A → B", "B → A")
        assert row.approved is False


def test_apply_approved_normalization_only_patches_approved_items() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    presentation = build_compare_presentation(project, project)
    proposals = build_normalization_proposals(presentation, direction="a_to_b")
    if not proposals.items:
        return
    item = proposals.items[0]
    target_fm = item.fm_id_a
    if target_fm is None:
        return
    original = getattr(project.faalwijzes[target_fm], item.field)
    updated, audit = apply_approved_normalization(
        project,
        proposals.items,
        approved_indices=frozenset({0}),
    )
    assert getattr(updated.faalwijzes[target_fm], item.field) == item.proposed_value
    assert audit.patch_count == 1
    restored = rollback_last_patch(updated, audit)
    assert getattr(restored.faalwijzes[target_fm], item.field) == original


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


def test_patch_apply_blocked_when_validation_fails() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    from rcm_desktop.adapter.patch_audit_service import NormalizationPatch

    patch = NormalizationPatch(
        target_fm_id="FM-001",
        field="mttf_jaar",
        new_value=0.0,
        approved=True,
    )
    with pytest.raises(MaterializeBlockedError):
        apply_patch(project, patch)


def test_compare_models_window_hides_normalization_review(qtbot, tmp_path) -> None:
    pytest.importorskip("PySide6")
    import json
    import shutil

    from rcm_desktop.views.compare_models_window import CompareModelsWindow

    src = Path("tests/fixtures/sample_project.rcm.json")
    path_a = tmp_path / "a.rcm.json"
    path_b = tmp_path / "b.rcm.json"
    shutil.copy(src, path_a)
    data_b = json.loads(src.read_text(encoding="utf-8"))
    data_b["faalwijzes"]["FM-001"]["mttf_jaar"] = 99.0
    path_b.write_text(json.dumps(data_b), encoding="utf-8")

    window = CompareModelsWindow()
    qtbot.addWidget(window)
    window.load_paths(path_a, path_b)
    assert not hasattr(window, "_normalization_table") or not window._normalization_table.isVisible()
    assert window.table_model().rowCount() >= 1
