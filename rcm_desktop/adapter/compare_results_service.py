"""Cache-hydrate en analytische runs voor dual-project compare (slice 96 issue 04)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rcm_core.models import FMResult

from rcm_desktop.adapter.compare_session_service import CompareSession
from rcm_desktop.adapter.run_service import RunResult, hydrate_run_from_cache, run as run_analytical


@dataclass(frozen=True)
class CompareSideStatus:
    side: str  # a | b
    source: str  # cache | run | none
    summary: str = ""


@dataclass(frozen=True)
class CompareResultsBundle:
    results_a: dict[str, FMResult]
    results_b: dict[str, FMResult]
    status_a: CompareSideStatus
    status_b: CompareSideStatus


def _results_dict(run: RunResult | None) -> dict[str, FMResult]:
    if run is None or run.status != "done":
        return {}
    return {fm.fm_id: fm for fm in run.fm_core_results}


def hydrate_compare_results(session: CompareSession) -> CompareResultsBundle:
    run_a = hydrate_run_from_cache(session.project_a, session.path_a)
    run_b = hydrate_run_from_cache(session.project_b, session.path_b)
    return CompareResultsBundle(
        results_a=_results_dict(run_a),
        results_b=_results_dict(run_b),
        status_a=CompareSideStatus("a", "cache" if run_a else "none"),
        status_b=CompareSideStatus("b", "cache" if run_b else "none"),
    )


def run_compare_analytical(
    session: CompareSession,
    *,
    side: Literal["a", "b", "both"],
    existing: CompareResultsBundle | None = None,
) -> CompareResultsBundle:
    base = existing or hydrate_compare_results(session)
    results_a = dict(base.results_a)
    results_b = dict(base.results_b)
    status_a = base.status_a
    status_b = base.status_b

    if side in ("a", "both"):
        run_a = run_analytical(session.project_a, session.path_a)
        if run_a.status == "done":
            results_a = _results_dict(run_a)
            status_a = CompareSideStatus("a", "run", run_a.summary)

    if side in ("b", "both"):
        run_b = run_analytical(session.project_b, session.path_b)
        if run_b.status == "done":
            results_b = _results_dict(run_b)
            status_b = CompareSideStatus("b", "run", run_b.summary)

    return CompareResultsBundle(
        results_a=results_a,
        results_b=results_b,
        status_a=status_a,
        status_b=status_b,
    )
