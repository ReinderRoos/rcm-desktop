"""FM-validatie — counterfactual expected_failures vs AW (ADR-0008 diagnostiek v1.1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from rcm_core.lifecycle_horizon import effective_lifecycle_end_age
from rcm_core.distributions import build_rev_schedule, expected_failures_lifecycle
from rcm_core.fm_parity_diagnostics import (
    aw_expected_failures,
    compute_fm_input_diagnostics,
    compute_rev_diagnostics,
)
from rcm_core.models import FMResult, PMTask, RCMProject, TaskType
from rcm_core.units import HOURS_PER_YEAR


@dataclass(frozen=True)
class FailureValidationRow:
    fm_id: str
    omschrijving: str
    failure_type: str
    # AW benchmark
    aw_total_w: float | None
    aw_total_w_err: float | None
    aw_outage_frequency: float | None
    aw_initial_age_years: float | None
    aw_mttf_years: float | None
    # RCM2 invoer
    current_age_years: float
    mttf_years: float
    repair_quality: float
    effective_multiplicity: float
    rev_moments_active: int
    rev_moments_structural: int
    cm_overlay_disabled_pm_count: int
    # Counterfactuals (# falen, incl. multipliciteit)
    ef_actual: float
    ef_cm_overlay: float
    ef_no_rev: float
    ef_rev_aw_100pct: float
    ef_rq_0: float
    ef_rq_0_5: float
    ef_rq_1: float
    ef_horizon_forward: float
    # Attributie (Δ t.o.v. AW waar mogelijk)
    delta_scenario: float | None
    delta_rev_effect: float | None
    delta_rev_pct: float | None
    delta_horizon: float | None
    delta_residual: float | None
    dominant_factor: str


@dataclass(frozen=True)
class FailureValidationReport:
    rows: tuple[FailureValidationRow, ...]
    lifecycle_years: float
    cm_overlay_pm_count: int


def _disabled_pm_ids(project: RCMProject) -> frozenset[str]:
    raw = (project.import_settings or {}).get("aw_disabled_pm_ids") or []
    if not isinstance(raw, list):
        return frozenset()
    return frozenset(str(x) for x in raw if x)


def _cause_meta(project: RCMProject) -> dict[str, object]:
    raw = (project.import_settings or {}).get("isograph_causes") or {}
    return raw if isinstance(raw, dict) else {}


def _hours_to_years(raw: object) -> float | None:
    if raw in (None, ""):
        return None
    return float(raw) / HOURS_PER_YEAR


def _float_or_none(raw: object) -> float | None:
    if raw in (None, ""):
        return None
    return float(raw)


def _pm_tasks_filtered(
    project: RCMProject,
    fm_id: str,
    *,
    disabled_pm_ids: frozenset[str],
    rev_aging_effect_pct: float | None = None,
) -> list[PMTask]:
    tasks = [
        task
        for task in project.get_pm_tasks_for_fm(fm_id)
        if task.pm_id not in disabled_pm_ids
    ]
    if rev_aging_effect_pct is None:
        return tasks
    out: list[PMTask] = []
    for task in tasks:
        if task.taak_type != TaskType.REV:
            out.append(task)
            continue
        data = task.to_dict()
        data["aging_effect_pct"] = rev_aging_effect_pct
        out.append(PMTask.from_dict(data))
    return out


def compute_expected_failures_for_fm(
    project: RCMProject,
    fm_id: str,
    *,
    disabled_pm_ids: frozenset[str] = frozenset(),
    repair_quality: float | None = None,
    no_rev: bool = False,
    rev_aging_effect_pct: float | None = None,
    horizon_forward: bool = False,
) -> float:
    """Verwacht aantal falen voor één FM met optionele parameter-overrides."""
    fm = project.faalwijzes.get(fm_id)
    if fm is None:
        return 0.0

    pbs = project.pbs_items.get(fm.pbs_id)
    if pbs is None:
        current_age = 0.0
        eff_multiplicity = 1.0
    else:
        eff_bouwjaar = pbs.effective_bouwjaar(project.pbs_items)
        current_age = (
            float(project.config.modeljaar - eff_bouwjaar) if eff_bouwjaar > 0 else 0.0
        )
        eff_multiplicity = pbs.effective_multiplicity(project.pbs_items)

    lifecycle_end = effective_lifecycle_end_age(
        float(project.config.lifecycle_years),
        current_age,
        aw_mc_horizon=horizon_forward or project.config.aw_mc_lifecycle_horizon,
    )

    rq = float(fm.repair_quality if repair_quality is None else repair_quality)

    pm_tasks = _pm_tasks_filtered(
        project,
        fm_id,
        disabled_pm_ids=disabled_pm_ids,
        rev_aging_effect_pct=rev_aging_effect_pct,
    )
    rev_schedule = (
        ()
        if no_rev or fm.failure_type.value != "aging"
        else build_rev_schedule(pm_tasks)
    )

    ef = expected_failures_lifecycle(
        current_age=current_age,
        lifecycle_years=lifecycle_end,
        failure_type=fm.failure_type.value,
        mttf=fm.mttf_jaar,
        sigma=fm.effective_sigma(project.config.default_sigma_fraction),
        aging_distribution=fm.aging_distribution.value,
        beta_jaar=fm.beta_jaar,
        repair_quality=rq,
        rev_schedule=rev_schedule,
    )
    return ef * eff_multiplicity


def _dominant_factor(
    *,
    delta_scenario: float | None,
    delta_rev_effect: float | None,
    delta_rev_pct: float | None,
    delta_horizon: float | None,
    delta_residual: float | None,
) -> str:
    labels = {
        "delta_scenario": "scenario (CM-overlay)",
        "delta_rev_effect": "REV in motor",
        "delta_rev_pct": "REV aging_effect import",
        "delta_horizon": "LifeTime-semantiek",
        "delta_residual": "residu (AW-onbekend)",
    }
    candidates = {
        "delta_scenario": delta_scenario,
        "delta_rev_effect": delta_rev_effect,
        "delta_rev_pct": delta_rev_pct,
        "delta_horizon": delta_horizon,
        "delta_residual": delta_residual,
    }
    scored = {k: abs(v) for k, v in candidates.items() if v is not None}
    if not scored:
        return "—"
    key = max(scored, key=scored.get)
    return labels.get(key, key)


def build_failure_validation_report(
    project: RCMProject,
    fm_results: Mapping[str, FMResult],
) -> FailureValidationReport:
    """Counterfactual-rapport per FM voor validatie-export."""
    cause_meta = _cause_meta(project)
    disabled = _disabled_pm_ids(project)
    lifecycle = float(project.config.lifecycle_years)
    rows: list[FailureValidationRow] = []

    for fm_id in sorted(fm_results):
        result = fm_results[fm_id]
        fm = project.faalwijzes.get(fm_id)
        meta = cause_meta.get(fm_id)
        meta_dict = meta if isinstance(meta, dict) else {}

        inputs = compute_fm_input_diagnostics(project, fm_id)
        rev = compute_rev_diagnostics(project, fm_id)
        aw_ef = aw_expected_failures(meta_dict, lifecycle_years=lifecycle)

        ef_actual = result.expected_failures
        ef_cm = compute_expected_failures_for_fm(
            project, fm_id, disabled_pm_ids=disabled
        )
        ef_no_rev = compute_expected_failures_for_fm(
            project, fm_id, disabled_pm_ids=disabled, no_rev=True
        )
        ef_rev_aw = compute_expected_failures_for_fm(
            project,
            fm_id,
            disabled_pm_ids=disabled,
            rev_aging_effect_pct=100.0,
        )
        ef_rq_0 = compute_expected_failures_for_fm(
            project, fm_id, disabled_pm_ids=disabled, repair_quality=0.0
        )
        ef_rq_0_5 = compute_expected_failures_for_fm(
            project, fm_id, disabled_pm_ids=disabled, repair_quality=0.5
        )
        ef_rq_1 = compute_expected_failures_for_fm(
            project, fm_id, disabled_pm_ids=disabled, repair_quality=1.0
        )
        ef_horizon = compute_expected_failures_for_fm(
            project, fm_id, disabled_pm_ids=disabled, horizon_forward=True
        )

        delta_scenario = ef_actual - ef_cm
        delta_rev_effect = ef_cm - ef_no_rev
        delta_rev_pct = ef_rev_aw - ef_no_rev
        delta_horizon = ef_horizon - ef_cm
        delta_residual = (aw_ef - ef_horizon) if aw_ef is not None else None

        pbs = project.pbs_items.get(fm.pbs_id) if fm is not None else None
        multiplicity = (
            pbs.effective_multiplicity(project.pbs_items) if pbs is not None else 1.0
        )

        rows.append(
            FailureValidationRow(
                fm_id=fm_id,
                omschrijving=fm.faalwijze_omschrijving if fm is not None else fm_id,
                failure_type=fm.failure_type.value if fm is not None else "—",
                aw_total_w=_float_or_none(meta_dict.get("TotalW")),
                aw_total_w_err=_float_or_none(meta_dict.get("TotalWErr")),
                aw_outage_frequency=_float_or_none(meta_dict.get("OutageFrequency")),
                aw_initial_age_years=_hours_to_years(meta_dict.get("InitialAge")),
                aw_mttf_years=_hours_to_years(meta_dict.get("FmMttf")),
                current_age_years=inputs.current_age_years,
                mttf_years=inputs.mttf_years,
                repair_quality=float(fm.repair_quality) if fm is not None else 1.0,
                effective_multiplicity=multiplicity,
                rev_moments_active=rev.active_moments,
                rev_moments_structural=rev.structural_moments,
                cm_overlay_disabled_pm_count=len(disabled),
                ef_actual=ef_actual,
                ef_cm_overlay=ef_cm,
                ef_no_rev=ef_no_rev,
                ef_rev_aw_100pct=ef_rev_aw,
                ef_rq_0=ef_rq_0,
                ef_rq_0_5=ef_rq_0_5,
                ef_rq_1=ef_rq_1,
                ef_horizon_forward=ef_horizon,
                delta_scenario=delta_scenario,
                delta_rev_effect=delta_rev_effect,
                delta_rev_pct=delta_rev_pct,
                delta_horizon=delta_horizon,
                delta_residual=delta_residual,
                dominant_factor=_dominant_factor(
                    delta_scenario=delta_scenario,
                    delta_rev_effect=delta_rev_effect,
                    delta_rev_pct=delta_rev_pct,
                    delta_horizon=delta_horizon,
                    delta_residual=delta_residual,
                ),
            )
        )

    return FailureValidationReport(
        rows=tuple(rows),
        lifecycle_years=lifecycle,
        cm_overlay_pm_count=len(disabled),
    )
