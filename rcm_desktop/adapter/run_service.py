from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rcm_core.incremental_run import run_incremental_analysis
from rcm_core.models import FMResult, RCMProject
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_run_materializer import materialize_project_for_overlay
from rcm_desktop.adapter.result_view_service import FMResultRow, PBSResultRow, build_pbs_rows, build_rows
from rcm_desktop.adapter.validate_service import UserFacingError


def _debug_log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    # #region agent log
    payload = {
        "sessionId": "224489",
        "runId": "analyse-run",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    log_path = Path(__file__).resolve().parents[2] / "debug-224489.log"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")
    # #endregion


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

    run_project = project
    if (
        planning_overlay is not None
        and planning_overlay.active
        and planning_overlay.disabled_pm_ids
    ):
        run_project = materialize_project_for_overlay(project, planning_overlay)

    try:
        result = run_incremental_analysis(
            run_project,
            Path(project_path),
            full_recompute=full_recompute,
            parallel=parallel,
            scenario_key=scenario_key,
        )
    except Exception:
        return RunResult(
            status="error",
            summary="Run mislukt door een interne fout.",
            metrics=RunMetrics(fm_result_count=0, total_lifecycle_faalmomenten=0.0, total_cost_eur=0.0),
            rows=[],
            pbs_rows=[],
            error=UserFacingError(
                code="RUN_INTERNAL_ERROR",
                message="Er ging iets mis tijdens de analyse-run.",
            ),
            fm_core_results=tuple(),
        )

    fm_results = list(result.fm_results.values())
    fm_core_tuple = tuple(fm_results)
    metrics = RunMetrics(
        fm_result_count=len(fm_results),
        total_lifecycle_faalmomenten=sum(item.expected_failures for item in fm_results),
        total_cost_eur=sum(item.total_cost_eur for item in fm_results),
        total_downtime_hr=sum(item.expected_total_downtime_hr + item.expected_pm_downtime_hr for item in fm_results),
        lifecycle_years=float(project.config.lifecycle_years),
        total_risk_contribution=sum(item.risk_contribution for item in fm_results),
    )
    rows = build_rows(run_project, fm_results)
    pbs_rows = build_pbs_rows(run_project, result.pbs_results)
    return RunResult(
        status="done",
        summary=f"Run voltooid met {metrics.fm_result_count} FM-resultaten.",
        metrics=metrics,
        rows=rows,
        pbs_rows=pbs_rows,
        fm_core_results=fm_core_tuple,
    )
