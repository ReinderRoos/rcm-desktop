"""Regressie — Gaarkeuken CM laadfout na uniformeren-patch (slice 95 / HILT PR #35)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.persistence import load_project
from rcm_core.validators import validate_project

from rcm_desktop.adapter.compare_balanced_presentation_service import build_compare_presentation
from rcm_desktop.adapter.entity_edit_service import EntityEditService
from rcm_desktop.adapter.fm_edit_commit_service import commit_edits, create_edit_session
from rcm_desktop.adapter.normalization_proposal_service import build_normalization_proposals
from rcm_desktop.adapter.patch_audit_service import (
    NormalizationPatch,
    apply_approved_normalization,
    apply_patch,
)
from rcm_desktop.adapter import validate_service

GAARKEUKEN_CM = Path("tests/fixtures/RCMCostdata export_Gaarkeuken_CM.rcm.rcm.json")
GAARKEUKEN_PM = Path("tests/fixtures/RCMCostdata export_Gaarkeuken_PM.rcm.rcm.json")
BROKEN_FM_ID = "06H-350.3.2.1.A.1"


@pytest.mark.skipif(not GAARKEUKEN_CM.is_file(), reason="Gaarkeuken CM fixture ontbreekt")
def test_gaarkeuken_cm_fixture_has_random_sigma_inconsistency() -> None:
    project = load_project(GAARKEUKEN_CM)
    errors = validate_project(project)
    assert any(error.code == "FM_RANDOM_SIGMA_NONZERO" for error in errors)
    fm = project.faalwijzes[BROKEN_FM_ID]
    assert fm.failure_type.value == "random"
    assert fm.sigma_jaar > 0


@pytest.mark.skipif(not GAARKEUKEN_CM.is_file(), reason="Gaarkeuken CM fixture ontbreekt")
def test_gaarkeuken_cm_validate_service_reports_invalid() -> None:
    result, _project = validate_service.run(GAARKEUKEN_CM)
    assert result.status == "invalid"
    assert any(detail.code == "FM_RANDOM_SIGMA_NONZERO" for detail in result.details)


@pytest.mark.skipif(not GAARKEUKEN_PM.is_file(), reason="Gaarkeuken PM fixture ontbreekt")
def test_commit_edits_blocks_random_failure_type_with_nonzero_sigma() -> None:
    project = load_project(GAARKEUKEN_PM)
    session = create_edit_session(project)
    grid = EntityEditService.for_view("input.faalwijzen")
    grid.attach_editing_session(session)
    grid.apply_change(BROKEN_FM_ID, "failure_type", "random")

    result = commit_edits(session, project_path=None, save_to_disk=False)

    assert result.ok is False
    assert result.project is None
    assert result.errors
    assert validate_project(project) == []


@pytest.mark.skipif(not GAARKEUKEN_PM.is_file(), reason="Gaarkeuken PM fixture ontbreekt")
def test_failure_type_patch_to_random_zeroes_sigma() -> None:
    project = load_project(GAARKEUKEN_PM)
    patch = NormalizationPatch(
        target_fm_id=BROKEN_FM_ID,
        field="failure_type",
        new_value="random",
        approved=True,
    )
    updated, audit = apply_patch(project, patch)

    fm = updated.faalwijzes[BROKEN_FM_ID]
    failure_type = fm.failure_type.value if hasattr(fm.failure_type, "value") else fm.failure_type
    assert failure_type == "random"
    assert fm.sigma_jaar == 0.0
    assert validate_project(updated) == []
    assert audit.patch_count == 1


@pytest.mark.skipif(
    not GAARKEUKEN_CM.is_file() or not GAARKEUKEN_PM.is_file(),
    reason="Gaarkeuken CM/PM fixtures ontbreken",
)
def test_gaarkeuken_cm_repair_via_pm_normalization() -> None:
    cm = load_project(GAARKEUKEN_CM)
    pm = load_project(GAARKEUKEN_PM)
    presentation = build_compare_presentation(cm, pm)
    proposals = build_normalization_proposals(presentation, direction="a_to_b")
    index = next(
        i
        for i, item in enumerate(proposals.items)
        if item.fm_id_a == BROKEN_FM_ID and item.field == "failure_type"
    )
    repaired, _audit = apply_approved_normalization(
        cm,
        proposals.items,
        approved_indices=frozenset({index}),
    )
    assert validate_project(repaired) == []
