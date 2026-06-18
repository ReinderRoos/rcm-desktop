from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rcm_core.cm_overlay import aw_disabled_pm_ids, materialize_cm_overlay_project
from rcm_core.engine import compute_pbs_results
from rcm_core.incremental_run import run_incremental_analysis
from rcm_core.models import FMResult, PBSResult, RCMProject
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_run_materializer import materialize_project_for_overlay
from rcm_desktop.adapter.result_view_service import FMResultRow, PBSResultRow, build_pbs_rows, build_rows
from rcm_desktop.adapter.adapter_error_handling import user_facing_from_exception
from rcm_desktop.adapter.validate_service import UserFacingError


@dataclass(frozen=True)
class RunMetrics:
    fm_result_count: int
    total_lifecycle_faalmomenten: float
    total_cost_eur: float
    total_downtime_hr: float = 0.0
    lifecycle_years: float = 0.0
    total_risk_contribution: float | None = None


@dataclass(frozen=True)
class RunResult:
    status: str
    summary: str
    metrics: RunMetrics
    rows: list[FMResultRow] = field(default_factory=list)
    pbs_rows: list[PBSResultRow] = field(default_factory=list)
    error: UserFacingError | None = None
    # Kern-FMResultaten voor LCC-builders; leeg bij error.
    fm_core_results: tuple[FMResult, ...] = field(default_factory=tuple)


def build_run_result(
    project: RCMProject,
    fm_results: list[FMResult],
    *,
    pbs_results: dict[str, PBSResult] | None = None,
    summary_prefix: str = "Run voltooid",
) -> RunResult:
    """Enige factory voor motor- en cache-RunResult."""
    if pbs_results is None:
        pbs_results = compute_pbs_results(project, {fr.fm_id: fr for fr in fm_results})
    metrics = RunMetrics(
        fm_result_count=len(fm_results),
        total_lifecycle_faalmomenten=sum(item.expected_failures for item in fm_results),
        total_cost_eur=sum(item.total_cost_eur for item in fm_results),
        total_downtime_hr=sum(
            item.expected_total_downtime_hr + item.expected_pm_downtime_hr for item in fm_results
        ),
        lifecycle_years=float(project.config.lifecycle_years),
        total_risk_contribution=sum(item.risk_contribution for item in fm_results),
    )
    return RunResult(
        status="done",
        summary=f"{summary_prefix} met {metrics.fm_result_count} FM-resultaten.",
        metrics=metrics,
        rows=build_rows(project, fm_results),
        pbs_rows=build_pbs_rows(project, pbs_results),
        fm_core_results=tuple(fm_results),
    )


def _resolve_run_project(
    project: RCMProject,
    planning_overlay: PlanningOverlayState | None,
) -> RCMProject:
    """Materialiseer disabled PM's: what-if overlay wanneer actief, anders AW-import CM-overlay."""
    if planning_overlay is not None and planning_overlay.active:
        if planning_overlay.disabled_pm_ids:
            return materialize_project_for_overlay(project, planning_overlay)
        return project
    disabled = aw_disabled_pm_ids(project)
    if disabled:
        return materialize_cm_overlay_project(project)
    return project


def hydrate_run_from_cache(project: RCMProject, project_path: str | Path) -> RunResult | None:
    from rcm_core.cache import find_affected_fms, load_cache_snapshot

    snap = load_cache_snapshot(project, Path(project_path))
    if not snap.global_layer_trusted or not snap.raw_results:
        return None
    if find_affected_fms(project, snap.hashes):
        return None
    fm_results = [FMResult.from_dict(raw) for raw in snap.raw_results.values()]
    if not fm_results:
        return None
    return build_run_result(project, fm_results, summary_prefix="Geladen uit cache")


def run(
    project: RCMProject | None,
    project_path: str | Path,
    *,
    full_recompute: bool = True,
    parallel: bool = False,
    scenario_key: str | None = None,
    planning_overlay: PlanningOverlayState | None = None,
) -> RunResult:
    if project is None:
        return RunResult(
            status="error",
            summary="Run niet gestart: project ontbreekt.",
            metrics=RunMetrics(fm_result_count=0, total_lifecycle_faalmomenten=0.0, total_cost_eur=0.0),
            rows=[],
            pbs_rows=[],
            error=UserFacingError(
                code="RUN_PRECONDITION_NOT_MET",
                message="Start eerst een geldige validate zodat een project geladen is.",
            ),
            fm_core_results=tuple(),
        )

    run_project = _resolve_run_project(project, planning_overlay)

    try:
        result = run_incremental_analysis(
            run_project,
            Path(project_path),
            full_recompute=full_recompute,
            parallel=parallel,
            scenario_key=scenario_key,
        )
    except Exception as exc:
        return RunResult(
            status="error",
            summary="Run mislukt door een interne fout.",
            metrics=RunMetrics(fm_result_count=0, total_lifecycle_faalmomenten=0.0, total_cost_eur=0.0),
            rows=[],
            pbs_rows=[],
            error=user_facing_from_exception(
                "rcm_desktop.adapter.run_service",
                code="RUN_INTERNAL_ERROR",
                message="Er ging iets mis tijdens de analyse-run.",
                exc=exc,
                context="run_incremental_analysis mislukt",
            ),
            fm_core_results=tuple(),
        )

    fm_results = list(result.fm_results.values())
    built = build_run_result(
        run_project,
        fm_results,
        pbs_results=result.pbs_results,
    )
    return RunResult(
        status="done",
        summary=built.summary,
        metrics=built.metrics,
        rows=built.rows,
        pbs_rows=built.pbs_rows,
        fm_core_results=built.fm_core_results,
    )
