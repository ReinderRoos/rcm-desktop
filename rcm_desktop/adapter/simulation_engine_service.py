"""Monte Carlo adapter facade over ``rcm_core.simulation_engine``."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from rcm_core.models import RCMProject
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
        rf = 0.0
        links = project.get_fm_effect_links_for_fm(fm_id)
        if links:
            rf = float(links[0].fractie)
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


def attach_mc_run_to_store(
    store: SimulationResultStore,
    mc_result: MCRunResult,
    *,
    job_id: str,
) -> None:
    """Persist MC job identity without touching analytical run slot."""
    store.set_mc_job_id(job_id)


def detach_mc_run(store: SimulationResultStore) -> None:
    store.set_mc_job_id("")
