"""Qt-free Monte Carlo workspace orchestration (slice 98 issues 06/10)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import RCMProject

from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.simulation_job_service import RunMode


def resolve_run_mode(data: object) -> RunMode:
    if isinstance(data, RunMode):
        return data
    return RunMode.ANALYTICAL


def start_analyse_uses_monte_carlo(run_mode: RunMode) -> bool:
    return run_mode is RunMode.MONTE_CARLO


@dataclass(frozen=True)
class MonteCarloRunParams:
    n: int
    seed: int | None


def monte_carlo_params_from_project(project: RCMProject) -> MonteCarloRunParams:
    cfg = project.config
    return MonteCarloRunParams(n=int(cfg.monte_carlo_n), seed=cfg.monte_carlo_seed)


def session_has_mc_bands(session: ProjectSession | None) -> bool:
    return (
        session is not None
        and session.mc_run is not None
        and session.mc_run.status == "done"
        and bool(session.mc_run.rows)
    )


def session_has_analytical_points(session: ProjectSession | None) -> bool:
    return session is not None and session.has_completed_run()


def top10_lcc_reads_analytical_slot(session: ProjectSession | None) -> bool:
    """Top 10 and LCC always use the analytical ``RunResult`` slot."""
    return session_has_analytical_points(session)


def fm_detail_source_for_run_mode(
    run_mode: RunMode,
    session: ProjectSession | None,
) -> str:
    if run_mode is RunMode.MONTE_CARLO:
        if session_has_mc_bands(session):
            return "mc_bands"
        if session is not None and session.mc_run is not None and session.mc_run.status == "cancelled":
            return "mc_cancelled"
        return "mc_empty"
    return "analytical"
