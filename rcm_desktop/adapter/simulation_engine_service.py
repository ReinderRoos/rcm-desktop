"""Monte Carlo adapter facade over ``rcm_core.simulation_engine``."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from rcm_core.engine import compute_detection_delay_hr, compute_pm_totals
from rcm_core.lcc_profile import build_fm_horizon_profile
from rcm_core.models import FMHorizonProfile, FMResult, Faalwijze, RCMProject
from rcm_core.simulation_engine import FMMCResult, MetricBand, SimulationEngine
from rcm_desktop.adapter.adapter_error_handling import user_facing_from_exception
from rcm_desktop.adapter.simulation_job_service import SimulationResultStore
from rcm_desktop.adapter.validate_service import UserFacingError


@dataclass(frozen=True)
class FMMCResultRow:
    fm_id: str
    faalwijze_omschrijving: str
    bouwdeel_naam: str
    failures_band: MetricBand
    downtime_band: MetricBand
    cost_band: MetricBand
    is_nmf: bool
    rf: float


@dataclass(frozen=True)
class MCRunResult:
    status: str
    seed: int
    n_completed: int
    fm_results: dict[str, FMMCResult] = field(default_factory=dict)
    rows: tuple[FMMCResultRow, ...] = field(default_factory=tuple)
    error: UserFacingError | None = None


def build_mc_fm_rows(
    project: RCMProject,
    fm_results: dict[str, FMMCResult],
) -> tuple[FMMCResultRow, ...]:
    rows: list[FMMCResultRow] = []
    for fm_id in project.faalwijzes:
        mc = fm_results.get(fm_id)
        if mc is None:
            continue
        fm = project.faalwijzes[fm_id]
        pbs = project.pbs_items.get(fm.pbs_id)
        bouwdeel = pbs.bouwdeel_naam if pbs is not None else ""
        from rcm_core.effect_impact_service import EffectNbFilterSet

        from rcm_desktop.adapter.result_view_service import _resolve_rf_for_fm

        rf, _ = _resolve_rf_for_fm(project, fm_id, EffectNbFilterSet())
        rows.append(
            FMMCResultRow(
                fm_id=fm_id,
                faalwijze_omschrijving=fm.faalwijze_omschrijving,
                bouwdeel_naam=bouwdeel,
                failures_band=mc.failures,
                downtime_band=mc.downtime_hr,
                cost_band=mc.total_cost_eur,
                is_nmf=not fm.is_evident,
                rf=rf,
            )
        )
    return tuple(rows)


def run_monte_carlo(
    project: RCMProject | None,
    *,
    n: int,
    seed: int | None = None,
    progress_cb: Callable[[int, int], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> MCRunResult:
    if project is None:
        return MCRunResult(
            status="error",
            seed=0,
            n_completed=0,
            error=UserFacingError(
                code="MC_PRECONDITION_NOT_MET",
                message="Start eerst een geldige validate zodat een project geladen is.",
            ),
        )
    if n < 100:
        return MCRunResult(
            status="error",
            seed=int(seed or 0),
            n_completed=0,
            error=UserFacingError(
                code="CFG_MC_N",
                message="monte_carlo_n moet minimaal 100 zijn.",
            ),
        )
    try:
        engine = SimulationEngine()
        fm_results = engine.run(
            project,
            n=n,
            seed=seed,
            progress_cb=progress_cb,
            cancel_check=cancel_check,
        )
    except Exception as exc:
        return MCRunResult(
            status="error",
            seed=int(seed or 0),
            n_completed=0,
            error=user_facing_from_exception(
                "rcm_desktop.adapter.simulation_engine_service",
                code="MC_INTERNAL_ERROR",
                message="Er ging iets mis tijdens de Monte Carlo-run.",
                exc=exc,
                context="SimulationEngine.run mislukt",
            ),
        )
    effective_seed = next(iter(fm_results.values())).seed if fm_results else int(seed or 0)
    n_completed = next(iter(fm_results.values())).n_completed if fm_results else 0
    if cancel_check is not None and cancel_check() and n_completed < n:
        return MCRunResult(
            status="cancelled",
            seed=effective_seed,
            n_completed=n_completed,
        )
    rows = build_mc_fm_rows(project, fm_results)
    return MCRunResult(
        status="done",
        seed=effective_seed,
        n_completed=n_completed,
        fm_results=fm_results,
        rows=rows,
    )


def _scale_profile_buckets(
    values: list[float],
    target: float,
    *,
    uniform_if_empty: bool = True,
) -> list[float]:
    total = float(sum(values))
    if total > 0.0 and target > 0.0:
        factor = target / total
        return [float(v) * factor for v in values]
    if uniform_if_empty and target > 0.0 and values:
        uniform = target / len(values)
        return [uniform for _ in values]
    return list(values)


def _horizon_profile_for_mc_p50_fm(
    project: RCMProject,
    fm: Faalwijze,
    *,
    expected_cm_cost_eur: float,
    expected_raw_downtime_hr: float,
    detection_total_hr: float,
    per_failure_detection_hr: float,
) -> FMHorizonProfile | None:
    """Analytische jaartoerekening-SSOT, geschaald naar MC P50 lifecycle-totalen."""
    pbs = project.pbs_items.get(fm.pbs_id)
    if pbs is None:
        return None
    pm_tasks = project.get_pm_tasks_for_fm(fm.fm_id)
    profile = build_fm_horizon_profile(
        config=project.config,
        fm=fm,
        pbs=pbs,
        pm_tasks=pm_tasks,
        all_pbs=project.pbs_items,
        hidden_nb_per_failure_hr=per_failure_detection_hr,
    )
    # Keep ``cor_eur`` on the analytical bucket spine (unscaled). Scaling CM buckets
    # to MC P50 lifecycle CM breaks ``kosten_scalar_for_fm`` per-year parity with
    # engine ``FMResult`` rows (slice 101 / HILT101).
    return FMHorizonProfile(
        cor_eur=list(profile.cor_eur),
        # Downtime/NB: no uniform fallback when analytical buckets are empty —
        # matches engine FMResult + nb_yearly_series (NMF zonder TST-interval).
        cor_downtime_hr=_scale_profile_buckets(
            profile.cor_downtime_hr,
            expected_raw_downtime_hr,
            uniform_if_empty=False,
        ),
        hidden_nb_hr=_scale_profile_buckets(
            profile.hidden_nb_hr,
            detection_total_hr,
            uniform_if_empty=False,
        ),
    )


def attach_mc_run_to_store(
    store: SimulationResultStore,
    mc_result: MCRunResult,
    *,
    job_id: str,
) -> None:
    """Persist MC job identity without touching analytical run slot."""
    store.set_mc_job_id(job_id)


def fm_results_from_mc_p50(project: RCMProject, mc: MCRunResult) -> list[FMResult]:
    """Build synthetic ``FMResult`` rows from MC P50 bands for aggregate presentation."""
    lifecycle = float(project.config.lifecycle_years)
    counted_groups: set[str] = set()
    pending: list[tuple] = []
    for fm_id in project.faalwijzes:
        mc_fm = mc.fm_results.get(fm_id)
        if mc_fm is None:
            continue
        fm = project.faalwijzes[fm_id]
        pm_tasks = project.get_pm_tasks_for_fm(fm_id)
        pm_cost, pm_downtime, _ = compute_pm_totals(
            pm_tasks,
            project.task_groups,
            lifecycle,
            counted_groups,
        )
        pending.append((fm, mc_fm, pm_cost, pm_downtime))

    results: list[FMResult] = []
    for fm, mc_fm, pm_cost, pm_downtime in pending:
        failures = mc_fm.failures.p50
        total_downtime = mc_fm.downtime_hr.p50
        total_cost = mc_fm.total_cost_eur.p50
        cm_cost = fm.cost_cm_eur * failures
        raw_hr = fm.downtime_per_failure.to_hours() * failures
        cm_and_detection = max(0.0, total_downtime - pm_downtime)
        detection_total_hr = max(0.0, cm_and_detection - raw_hr)
        per_failure_detection = detection_total_hr / failures if failures > 0 else 0.0
        links = project.get_fm_effect_links_for_fm(fm.fm_id)
        risk = failures * float(links[0].fractie) if links else 0.0
        detection_delay_hr = compute_detection_delay_hr(fm, project.get_pm_tasks_for_fm(fm.fm_id))
        if detection_delay_hr == float("inf"):
            detection_delay_hr = 0.0
        horizon_profile = _horizon_profile_for_mc_p50_fm(
            project,
            fm,
            expected_cm_cost_eur=cm_cost,
            expected_raw_downtime_hr=raw_hr,
            detection_total_hr=detection_total_hr,
            per_failure_detection_hr=per_failure_detection if per_failure_detection > 0.0 else detection_delay_hr,
        )
        results.append(
            FMResult(
                fm_id=fm.fm_id,
                pbs_id=mc_fm.pbs_id,
                p_failure_lifecycle=min(1.0, failures),
                expected_failures=failures,
                expected_raw_downtime_hr=raw_hr,
                expected_detection_delay_hr=per_failure_detection,
                expected_total_downtime_hr=raw_hr + detection_total_hr,
                expected_pm_downtime_hr=pm_downtime,
                expected_cm_cost_eur=cm_cost,
                pm_cost_eur=pm_cost,
                total_cost_eur=total_cost,
                risk_contribution=risk,
                horizon_profile=horizon_profile,
            )
        )
    return results


def build_run_result_from_mc_p50(project: RCMProject, mc: MCRunResult):
    """Roll up MC P50 bands into a ``RunResult`` for Top 10 / LCC presentation."""
    from rcm_desktop.adapter.run_service import build_run_result

    if mc.status != "done":
        raise ValueError("MC run not completed")
    fm_results = fm_results_from_mc_p50(project, mc)
    return build_run_result(project, fm_results, summary_prefix="Monte Carlo P50")


def detach_mc_run(store: SimulationResultStore) -> None:
    store.set_mc_job_id("")
