"""Slice 52 — Modelinstellingen (adapter + kern)."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.cache import compute_global_digest
from rcm_core.config import RCMConfig
from rcm_core.models import FailureType, Faalwijze, Functie, PBSItem, RCMProject
from rcm_core.persistence import load_project, save_project
from rcm_desktop.adapter.isograph_import_service import build_from_sheets
from rcm_desktop.adapter.model_settings_service import (
    apply_default_aging_to_fms,
    build_draft,
    commit_model_settings,
    compute_requires_rerun,
    validate_draft,
)


def _minimal_project(**config_kw) -> RCMProject:
    cfg = RCMConfig(lifecycle_years=80.0, modeljaar=2026, **config_kw)
    pbs = PBSItem("PBS-1", "Obj", "El", "BD", bouwjaar=2000)
    func = Functie("F-1", "PBS-1", "Functie")
    aging = Faalwijze(
        "FM-A",
        "PBS-1",
        "F-1",
        "Aging",
        failure_type=FailureType.AGING,
        mttf_jaar=20.0,
        sigma_jaar=0.0,
    )
    random_fm = Faalwijze(
        "FM-R",
        "PBS-1",
        "F-1",
        "Random",
        failure_type=FailureType.RANDOM,
        mttf_jaar=10.0,
    )
    return RCMProject(
        config=cfg,
        pbs_items={"PBS-1": pbs},
        functies={"F-1": func},
        faalwijzes={"FM-A": aging, "FM-R": random_fm},
    )


class TestProjectMetadataPersistence:
    def test_metadata_roundtrip(self, tmp_path: Path) -> None:
        project = _minimal_project()
        project.projectnaam = "Demo AWZI"
        project.modelleur = "Analist X"
        path = tmp_path / "meta.rcm.json"
        save_project(project, path)
        restored = load_project(path)
        assert restored.projectnaam == "Demo AWZI"
        assert restored.modelleur == "Analist X"


class TestDigestExcludesMetadata:
    def test_different_metadata_same_digest(self) -> None:
        base = _minimal_project()
        other = copy.deepcopy(base)
        other.projectnaam = "Andere naam"
        other.modelleur = "Andere modelleur"
        assert compute_global_digest(base) == compute_global_digest(other)


class TestModelSettingsService:
    def test_metadata_only_change_does_not_require_rerun(self) -> None:
        project = _minimal_project()
        baseline = build_draft(project)
        draft = type(baseline)(
            projectnaam="Nieuw",
            modelleur=baseline.modelleur,
            lifecycle_years=baseline.lifecycle_years,
            modeljaar=baseline.modeljaar,
            default_mttf_multiplier=baseline.default_mttf_multiplier,
            default_sigma_fraction=baseline.default_sigma_fraction,
            default_aging_distribution=baseline.default_aging_distribution,
            default_beta_jaar=baseline.default_beta_jaar,
            monte_carlo_n=baseline.monte_carlo_n,
            monte_carlo_seed=baseline.monte_carlo_seed,
        )
        assert not compute_requires_rerun(baseline, draft)

    def test_lifecycle_change_requires_rerun(self) -> None:
        project = _minimal_project()
        baseline = build_draft(project)
        draft = type(baseline)(**{**baseline.__dict__, "lifecycle_years": 60.0})
        assert compute_requires_rerun(baseline, draft)

    def test_commit_metadata_only(self, tmp_path: Path) -> None:
        project = _minimal_project()
        baseline = build_draft(project)
        draft = type(baseline)(
            projectnaam="Rapportage",
            modelleur="M",
            lifecycle_years=baseline.lifecycle_years,
            modeljaar=baseline.modeljaar,
            default_mttf_multiplier=baseline.default_mttf_multiplier,
            default_sigma_fraction=baseline.default_sigma_fraction,
            default_aging_distribution=baseline.default_aging_distribution,
            default_beta_jaar=baseline.default_beta_jaar,
            monte_carlo_n=baseline.monte_carlo_n,
            monte_carlo_seed=baseline.monte_carlo_seed,
        )
        path = tmp_path / "proj.rcm.json"
        save_project(project, path)
        result = commit_model_settings(
            project,
            draft,
            baseline=baseline,
            project_path=path,
            save_to_disk=True,
        )
        assert result.ok
        assert result.project is not None
        assert not result.requires_rerun
        restored = load_project(path)
        assert restored.projectnaam == "Rapportage"


class TestApplyDefaultAging:
    def test_apply_only_aging_fms(self) -> None:
        project = _minimal_project()
        draft = build_draft(project)
        draft = type(draft)(
            **{
                **draft.__dict__,
                "default_aging_distribution": "weibull_2p",
                "default_beta_jaar": 2.5,
            }
        )
        updated, result = apply_default_aging_to_fms(project, draft)
        assert result.count == 1
        assert updated.faalwijzes["FM-A"].aging_distribution.value == "weibull_2p"
        assert updated.faalwijzes["FM-R"].failure_type == FailureType.RANDOM


class TestImportProjectnaamPrefill:
    def test_prefill_from_description(self) -> None:
        sheets = {
            "Project": [{"Description": "Gaarkeuken demo", "LifeTime": 700800.0}],
            "RcmLocations": [],
            "RcmCauses": [],
            "RcmFunctions": [],
            "RcmFunctionalFailures": [],
            "RcmCorrectiveTasks": [],
            "RcmEffects": [],
            "RcmCauseEffectAssignments": [],
            "RcmScheduledTasks": [],
            "TaskGroups": [],
        }
        result = build_from_sheets(sheets, modeljaar=2026)
        assert result.project.projectnaam == "Gaarkeuken demo"


pytest.importorskip("PySide6")


def test_dialog_accepts_metadata_change() -> None:
    from PySide6.QtWidgets import QApplication

    from rcm_desktop.views.model_settings_dialog import ModelSettingsDialog

    _ = QApplication.instance() or QApplication([])
    project = _minimal_project()
    dialog = ModelSettingsDialog(None, project=project, save_to_disk=False)
    dialog._projectnaam.setText("Smoke test")
    dialog._on_accept()
    assert dialog.commit_result is not None
    assert dialog.commit_result.ok
    assert dialog.commit_result.project.projectnaam == "Smoke test"
