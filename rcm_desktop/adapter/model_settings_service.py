"""Qt-vrije orchestratie voor Modelinstellingen-dialoog (slice 52)."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path

from rcm_core.models import AgingDistribution, FailureType, RCMProject
from rcm_core.validators import validate_project
from rcm_core.incremental_run import run_incremental_analysis

from rcm_desktop.adapter.adapter_error_handling import log_adapter_exception
from rcm_desktop.adapter.run_service import RunResult, build_run_result
from rcm_desktop.adapter.save_service import SaveConflictError, save_project_atomically


@dataclass(frozen=True)
class ModelSettingsDraft:
    projectnaam: str
    modelleur: str
    lifecycle_years: float
    modeljaar: int
    aw_mc_lifecycle_horizon: bool
    default_mttf_multiplier: float
    default_sigma_fraction: float
    default_aging_distribution: str
    default_beta_jaar: float
    monte_carlo_n: int
    monte_carlo_seed: int | None


@dataclass(frozen=True)
class ApplyAgingResult:
    count: int
    fm_ids: tuple[str, ...]


@dataclass(frozen=True)
class ModelSettingsCommitResult:
    ok: bool
    errors: tuple[str, ...]
    project: RCMProject | None
    requires_rerun: bool
    run_result: RunResult | None


def build_draft(project: RCMProject) -> ModelSettingsDraft:
    cfg = project.config
    return ModelSettingsDraft(
        projectnaam=project.projectnaam,
        modelleur=project.modelleur,
        lifecycle_years=float(cfg.lifecycle_years),
        modeljaar=int(cfg.modeljaar),
        aw_mc_lifecycle_horizon=bool(cfg.aw_mc_lifecycle_horizon),
        default_mttf_multiplier=float(cfg.default_mttf_multiplier),
        default_sigma_fraction=float(cfg.default_sigma_fraction),
        default_aging_distribution=str(cfg.default_aging_distribution or "normal"),
        default_beta_jaar=float(cfg.default_beta_jaar),
        monte_carlo_n=int(cfg.monte_carlo_n),
        monte_carlo_seed=cfg.monte_carlo_seed,
    )


def validate_draft(draft: ModelSettingsDraft) -> tuple[str, ...]:
    errors: list[str] = []
    if draft.lifecycle_years <= 0:
        errors.append("LCC-periode moet groter zijn dan 0.")
    if draft.default_mttf_multiplier <= 0:
        errors.append("MTTF-multiplier moet groter zijn dan 0.")
    if draft.default_sigma_fraction <= 0:
        errors.append("Sigma-fractie moet groter zijn dan 0.")
    valid_aging = {"normal", "truncated_normal_0", "weibull_2p"}
    if draft.default_aging_distribution not in valid_aging:
        errors.append("Ongeldige default verouderingsdistributie.")
    if draft.monte_carlo_n < 100:
        errors.append("monte_carlo_n moet minimaal 100 zijn.")
    if (
        draft.default_aging_distribution == "weibull_2p"
        and draft.default_beta_jaar <= 0
    ):
        errors.append("Default beta moet groter zijn dan 0 bij Weibull 2p.")
    return tuple(errors)


def compute_requires_rerun(
    baseline: ModelSettingsDraft,
    draft: ModelSettingsDraft,
    *,
    aging_fm_ids_applied: tuple[str, ...] = (),
) -> bool:
    if aging_fm_ids_applied:
        return True
    motor_fields = (
        "lifecycle_years",
        "modeljaar",
        "aw_mc_lifecycle_horizon",
        "default_mttf_multiplier",
        "default_sigma_fraction",
        "default_aging_distribution",
        "default_beta_jaar",
        "monte_carlo_n",
        "monte_carlo_seed",
    )
    for name in motor_fields:
        if getattr(baseline, name) != getattr(draft, name):
            return True
    return False


def apply_draft_to_project(project: RCMProject, draft: ModelSettingsDraft) -> RCMProject:
    updated = copy.deepcopy(project)
    updated.projectnaam = draft.projectnaam
    updated.modelleur = draft.modelleur
    updated.config.lifecycle_years = float(draft.lifecycle_years)
    updated.config.modeljaar = int(draft.modeljaar)
    updated.config.aw_mc_lifecycle_horizon = bool(draft.aw_mc_lifecycle_horizon)
    updated.config.default_mttf_multiplier = float(draft.default_mttf_multiplier)
    updated.config.default_sigma_fraction = float(draft.default_sigma_fraction)
    updated.config.default_aging_distribution = draft.default_aging_distribution
    updated.config.default_beta_jaar = float(draft.default_beta_jaar)
    updated.config.monte_carlo_n = int(draft.monte_carlo_n)
    updated.config.monte_carlo_seed = draft.monte_carlo_seed
    return updated


def count_aging_faalwijzen(project: RCMProject) -> int:
    return sum(
        1 for fm in project.faalwijzes.values() if fm.failure_type == FailureType.AGING
    )


def apply_default_aging_to_fms(
    project: RCMProject,
    draft: ModelSettingsDraft,
) -> tuple[RCMProject, ApplyAgingResult]:
    updated = copy.deepcopy(project)
    dist = AgingDistribution(draft.default_aging_distribution)
    fm_ids: list[str] = []
    for fm_id, fm in updated.faalwijzes.items():
        if fm.failure_type != FailureType.AGING:
            continue
        fm.aging_distribution = dist
        if dist == AgingDistribution.WEIBULL_2P:
            fm.beta_jaar = float(draft.default_beta_jaar)
        fm_ids.append(fm_id)
    return updated, ApplyAgingResult(count=len(fm_ids), fm_ids=tuple(sorted(fm_ids)))


def dialog_title(project: RCMProject, project_path: Path | str | None) -> str:
    if project.projectnaam.strip():
        label = project.projectnaam.strip()
    elif project_path:
        label = Path(project_path).name
    else:
        label = "project"
    return f"Modelinstellingen — {label}"


def commit_model_settings(
    project: RCMProject,
    draft: ModelSettingsDraft,
    *,
    baseline: ModelSettingsDraft,
    project_path: str | Path | None = None,
    save_to_disk: bool = False,
    baseline_mtime_ns: int | None = None,
    working_project: RCMProject | None = None,
    aging_fm_ids_applied: tuple[str, ...] = (),
    run_after_commit: bool = False,
) -> ModelSettingsCommitResult:
    draft_errors = validate_draft(draft)
    if draft_errors:
        return ModelSettingsCommitResult(
            ok=False,
            errors=draft_errors,
            project=None,
            requires_rerun=False,
            run_result=None,
        )

    built = apply_draft_to_project(
        working_project if working_project is not None else project,
        draft,
    )

    validation_errors = validate_project(built)
    if validation_errors:
        return ModelSettingsCommitResult(
            ok=False,
            errors=tuple(e.message for e in validation_errors),
            project=None,
            requires_rerun=False,
            run_result=None,
        )

    requires_rerun = compute_requires_rerun(
        baseline, draft, aging_fm_ids_applied=aging_fm_ids_applied
    )

    path_obj = Path(project_path) if project_path else None
    if save_to_disk and path_obj is not None:
        try:
            save_project_atomically(
                built,
                path_obj,
                baseline_mtime_ns=baseline_mtime_ns,
                check_conflict=True,
            )
        except SaveConflictError:
            return ModelSettingsCommitResult(
                ok=False,
                errors=("Bestand is extern gewijzigd sinds laden.",),
                project=None,
                requires_rerun=False,
                run_result=None,
            )

    run_result: RunResult | None = None
    if run_after_commit and requires_rerun and path_obj is not None:
        try:
            incremental = run_incremental_analysis(
                built,
                path_obj,
                full_recompute=False,
            )
            run_result = build_run_result(
                built,
                list(incremental.fm_results.values()),
                pbs_results=incremental.pbs_results,
                summary_prefix="Modelinstellingen opgeslagen",
            )
        except Exception as exc:
            log_adapter_exception(
                "rcm_desktop.adapter.model_settings_service",
                exc,
                context="incrementele analyse na modelinstellingen mislukt",
            )
            return ModelSettingsCommitResult(
                ok=False,
                errors=("Incrementele analyse mislukt.",),
                project=None,
                requires_rerun=requires_rerun,
                run_result=None,
            )

    return ModelSettingsCommitResult(
        ok=True,
        errors=(),
        project=built,
        requires_rerun=requires_rerun,
        run_result=run_result,
    )
