"""Monte Carlo simulation engine — Qt-free, no disk I/O."""
from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from rcm_core.config import RCMConfig
from rcm_core.distributions import (
    RevSchedule,
    _conditional_failures_with_rev_segments,
    _weibull_cdf,
    _weibull_eta_from_mttf_beta,
    build_rev_schedule,
    rejuvenate_age,
    sample_time_to_failure,
)
from rcm_core.engine import compute_detection_delay_hr, compute_pm_totals
from rcm_core.lifecycle_horizon import effective_lifecycle_end_age, study_duration_years
from rcm_core.models import AgingDistribution, FailureType, Faalwijze, PBSItem, RCMProject
from rcm_core.normal_fast import truncated_normal_conditional_mean


@dataclass(frozen=True)
class MetricBand:
    p10: float
    p50: float
    p90: float


@dataclass(frozen=True)
class FMMCResult:
    fm_id: str
    pbs_id: str
    failures: MetricBand
    downtime_hr: MetricBand
    total_cost_eur: MetricBand
    n_completed: int
    seed: int


ProgressCallback = Callable[[int, int], None]
CancelCheck = Callable[[], bool]


def _metric_band(values: list[float]) -> MetricBand:
    if not values:
        return MetricBand(p10=0.0, p50=0.0, p90=0.0)
    arr = np.asarray(values, dtype=float)
    return MetricBand(
        p10=float(np.percentile(arr, 10)),
        p50=float(np.percentile(arr, 50)),
        p90=float(np.percentile(arr, 90)),
    )


def _resolve_effective_seed(seed: int | None, rng: np.random.Generator) -> int:
    if seed is not None:
        return int(seed)
    return int(rng.integers(0, 2**31))


def _fm_study_context(
    fm: Faalwijze,
    pbs: PBSItem,
    config: RCMConfig,
    all_pbs: dict[str, PBSItem],
) -> tuple[float, float, float, float]:
    eff_bouwjaar = pbs.effective_bouwjaar(all_pbs)
    current_age = float(config.modeljaar - eff_bouwjaar) if eff_bouwjaar > 0 else 0.0
    eff_multiplicity = pbs.effective_multiplicity(all_pbs)
    lifecycle = effective_lifecycle_end_age(
        float(config.lifecycle_years),
        current_age,
        aw_mc_horizon=config.aw_mc_lifecycle_horizon,
    )
    duration = study_duration_years(
        float(config.lifecycle_years),
        current_age,
        aw_mc_horizon=config.aw_mc_lifecycle_horizon,
    )
    return current_age, duration, eff_multiplicity, lifecycle


def _simulate_random_failures_count(
    *,
    study_duration_years: float,
    mttf: float,
    rng: np.random.Generator,
) -> int:
    if mttf <= 0 or study_duration_years <= 0:
        return 0
    clock = 0.0
    count = 0
    while True:
        ttf = float(
            sample_time_to_failure(
                0.0,
                failure_type="random",
                mttf=mttf,
                sigma=0.0,
                rng=rng,
            )
        )
        clock += ttf
        if clock > study_duration_years:
            break
        count += 1
    return count


def _simulate_aging_failures_count(
    *,
    current_age: float,
    study_duration_years: float,
    mttf: float,
    sigma: float,
    repair_quality: float,
    aging_distribution: str,
    beta_jaar: float,
    rev_schedule: RevSchedule,
    rng: np.random.Generator,
    max_iterations: int = 100,
) -> int:
    """Stochastic aging path — SSOT loop aligned with ``test_aging_monte_carlo``."""
    if mttf <= 0 or study_duration_years <= 0:
        return 0

    if aging_distribution == AgingDistribution.WEIBULL_2P.value and not rev_schedule:
        f_start = _weibull_cdf(current_age, mttf=mttf, beta=beta_jaar)
        f_end = _weibull_cdf(current_age + study_duration_years, mttf=mttf, beta=beta_jaar)
        survival = 1.0 - f_start
        if survival < 1e-10:
            return 0
        expected = max(0.0, (f_end - f_start) / survival)
        return int(rng.poisson(expected))

    sig = float(sigma) if sigma > 0 else 0.15 * float(mttf)
    count = 0
    clock_time = 0.0
    effective_age = float(current_age)

    for _ in range(max_iterations):
        rem_clock = study_duration_years - clock_time
        if rem_clock <= 0:
            break

        age_at_lifecycle_end = effective_age + rem_clock
        p_fail = _conditional_failures_with_rev_segments(
            effective_age,
            clock_start=clock_time,
            rem_clock=rem_clock,
            mttf=mttf,
            sigma=sig,
            aging_distribution=aging_distribution,
            beta_jaar=beta_jaar,
            rev_schedule=rev_schedule,
        )
        if p_fail < 1e-10:
            break

        count += int(rng.poisson(p_fail))

        if aging_distribution == AgingDistribution.WEIBULL_2P.value:
            f_lo = _weibull_cdf(effective_age, mttf=mttf, beta=beta_jaar)
            f_hi = _weibull_cdf(age_at_lifecycle_end, mttf=mttf, beta=beta_jaar)
            p_mid = min(1.0 - 1e-12, max(0.0, 0.5 * (f_lo + f_hi)))
            eta = _weibull_eta_from_mttf_beta(mttf, beta_jaar)
            expected_failure_age = float(
                eta * ((-math.log(1.0 - p_mid)) ** (1.0 / float(beta_jaar)))
            )
        else:
            expected_failure_age = truncated_normal_conditional_mean(
                effective_age, age_at_lifecycle_end, mttf, sig
            )
        time_to_failure = expected_failure_age - effective_age
        clock_time += time_to_failure
        effective_age = rejuvenate_age(expected_failure_age, repair_quality)

    return count


def _path_metrics_from_failures(
    fm: Faalwijze,
    *,
    failures: float,
    pm_tasks: list,
    pm_cost_eur: float,
    pm_downtime_hr: float,
) -> tuple[float, float, float]:
    detection_delay_hr = compute_detection_delay_hr(fm, pm_tasks)
    if detection_delay_hr == float("inf"):
        detection_delay_hr = 0.0

    raw_downtime_hr = fm.downtime_per_failure.to_hours() * failures
    detection_total_hr = detection_delay_hr * failures
    downtime_hr = raw_downtime_hr + detection_total_hr + pm_downtime_hr
    cm_cost_eur = fm.cost_cm_eur * failures
    total_cost_eur = cm_cost_eur + pm_cost_eur
    return failures, downtime_hr, total_cost_eur


def _simulate_fm_failures(
    fm: Faalwijze,
    *,
    current_age: float,
    study_duration_years: float,
    eff_multiplicity: float,
    default_sigma_fraction: float,
    rev_schedule: RevSchedule,
    rng: np.random.Generator,
) -> float:
    sigma = fm.effective_sigma(default_sigma_fraction)
    aging_dist = fm.aging_distribution.value

    if fm.failure_type == FailureType.RANDOM:
        raw_failures = _simulate_random_failures_count(
            study_duration_years=study_duration_years,
            mttf=fm.mttf_jaar,
            rng=rng,
        )
    else:
        raw_failures = _simulate_aging_failures_count(
            current_age=current_age,
            study_duration_years=study_duration_years,
            mttf=fm.mttf_jaar,
            sigma=sigma,
            repair_quality=fm.repair_quality,
            aging_distribution=aging_dist,
            beta_jaar=fm.beta_jaar,
            rev_schedule=rev_schedule,
            rng=rng,
        )

    return raw_failures * eff_multiplicity


def _simulate_iteration(
    project: RCMProject,
    fm_contexts: list[dict],
    *,
    rng: np.random.Generator,
) -> dict[str, tuple[float, float, float]]:
    failure_counts: dict[str, float] = {}
    for ctx in fm_contexts:
        fm = ctx["fm"]
        failure_counts[fm.fm_id] = _simulate_fm_failures(
            fm,
            current_age=ctx["current_age"],
            study_duration_years=ctx["study_duration"],
            eff_multiplicity=ctx["eff_multiplicity"],
            default_sigma_fraction=project.config.default_sigma_fraction,
            rev_schedule=ctx["rev_schedule"],
            rng=rng,
        )

    counted_groups: set[str] = set()
    path_metrics: dict[str, tuple[float, float, float]] = {}
    for ctx in fm_contexts:
        fm = ctx["fm"]
        pm_cost, pm_downtime_hr, _ = compute_pm_totals(
            ctx["pm_tasks"],
            project.task_groups,
            ctx["lifecycle"],
            counted_groups,
        )
        path_metrics[fm.fm_id] = _path_metrics_from_failures(
            fm,
            failures=failure_counts[fm.fm_id],
            pm_tasks=ctx["pm_tasks"],
            pm_cost_eur=pm_cost,
            pm_downtime_hr=pm_downtime_hr,
        )
    return path_metrics


class SimulationEngine:
    """Monte Carlo engine entry point for adapter workers."""

    def run(
        self,
        project: RCMProject,
        *,
        n: int,
        seed: int | None = None,
        progress_cb: ProgressCallback | None = None,
        cancel_check: CancelCheck | None = None,
    ) -> dict[str, FMMCResult]:
        if n <= 0:
            raise ValueError("n must be positive")

        bootstrap_rng = np.random.default_rng()
        effective_seed = _resolve_effective_seed(seed, bootstrap_rng)
        rng = np.random.default_rng(effective_seed)

        fm_contexts: list[dict] = []
        for fm_id in project.faalwijzes:
            fm = project.faalwijzes[fm_id]
            pbs = project.pbs_items.get(fm.pbs_id)
            if pbs is None:
                continue
            current_age, study_duration, eff_multiplicity, lifecycle = _fm_study_context(
                fm, pbs, project.config, project.pbs_items
            )
            pm_tasks = project.get_pm_tasks_for_fm(fm.fm_id)
            rev_schedule = (
                build_rev_schedule(pm_tasks)
                if fm.failure_type == FailureType.AGING
                else ()
            )
            fm_contexts.append(
                {
                    "fm": fm,
                    "current_age": current_age,
                    "study_duration": study_duration,
                    "eff_multiplicity": eff_multiplicity,
                    "lifecycle": lifecycle,
                    "pm_tasks": pm_tasks,
                    "rev_schedule": rev_schedule,
                    "failure_samples": [],
                    "downtime_samples": [],
                    "cost_samples": [],
                }
            )

        completed = 0
        for _iteration in range(n):
            if cancel_check is not None and cancel_check():
                break

            path_metrics = _simulate_iteration(project, fm_contexts, rng=rng)
            for ctx in fm_contexts:
                fm_id = ctx["fm"].fm_id
                path_failures, path_downtime, path_cost = path_metrics[fm_id]
                ctx["failure_samples"].append(path_failures)
                ctx["downtime_samples"].append(path_downtime)
                ctx["cost_samples"].append(path_cost)

            completed += 1
            if progress_cb is not None:
                progress_cb(completed, n)

        results: dict[str, FMMCResult] = {}
        for ctx in fm_contexts:
            fm = ctx["fm"]
            results[fm.fm_id] = FMMCResult(
                fm_id=fm.fm_id,
                pbs_id=fm.pbs_id,
                failures=_metric_band(ctx["failure_samples"]),
                downtime_hr=_metric_band(ctx["downtime_samples"]),
                total_cost_eur=_metric_band(ctx["cost_samples"]),
                n_completed=completed,
                seed=effective_seed,
            )

        return results
