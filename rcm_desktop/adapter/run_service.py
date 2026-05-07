from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rcm_core.incremental_run import run_incremental_analysis
from rcm_core.models import RCMProject
from rcm_desktop.adapter.validate_service import UserFacingError


@dataclass(frozen=True)
class RunMetrics:
    fm_result_count: int
    total_lifecycle_faalmomenten: float
    total_cost_eur: float


@dataclass(frozen=True)
class RunResult:
    status: str
    summary: str
    metrics: RunMetrics
    error: UserFacingError | None = None


def run(
    project: RCMProject | None,
    project_path: str | Path,
    *,
    full_recompute: bool = True,
    parallel: bool = False,
) -> RunResult:
    if project is None:
        return RunResult(
            status="error",
            summary="Run niet gestart: project ontbreekt.",
            metrics=RunMetrics(fm_result_count=0, total_lifecycle_faalmomenten=0.0, total_cost_eur=0.0),
            error=UserFacingError(
                code="RUN_PRECONDITION_NOT_MET",
                message="Start eerst een geldige validate zodat een project geladen is.",
            ),
        )

    try:
        result = run_incremental_analysis(
            project,
            Path(project_path),
            full_recompute=full_recompute,
            parallel=parallel,
        )
    except Exception:
        return RunResult(
            status="error",
            summary="Run mislukt door een interne fout.",
            metrics=RunMetrics(fm_result_count=0, total_lifecycle_faalmomenten=0.0, total_cost_eur=0.0),
            error=UserFacingError(
                code="RUN_INTERNAL_ERROR",
                message="Er ging iets mis tijdens de analyse-run.",
            ),
        )

    fm_results = list(result.fm_results.values())
    metrics = RunMetrics(
        fm_result_count=len(fm_results),
        total_lifecycle_faalmomenten=sum(item.expected_failures for item in fm_results),
        total_cost_eur=sum(item.total_cost_eur for item in fm_results),
    )
    return RunResult(
        status="done",
        summary=f"Run voltooid met {metrics.fm_result_count} FM-resultaten.",
        metrics=metrics,
    )
