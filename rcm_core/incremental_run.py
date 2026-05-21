"""
Gedeelde orchestratie: incrementele of volledige analytische run + cache.

Caller moet eerst structurele validatie hebben gedaan (bijv. ``validate_project``);
deze module gaat uit van een consistent ``RCMProject``.
"""
from __future__ import annotations

import os
from concurrent.futures.process import BrokenProcessPool
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from rcm_core.cache import compute_fm_hash, find_affected_fms, load_cache_snapshot, merge_results, save_cache
from rcm_core.engine import compute_pbs_results, run_analytical
from rcm_core.models import FMResult, RCMProject

if TYPE_CHECKING:
    from rcm_core.models import PBSResult


def _limit_blas_threads_for_parallel() -> None:
    """Beperk BLAS-threading bij parallelle process pools (zelfde beleid als CLI)."""
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")


def _build_fm_hashes(project: RCMProject) -> dict[str, str]:
    new_hashes: dict[str, str] = {}
    for fm_id, fm in project.faalwijzes.items():
        pbs = project.pbs_items.get(fm.pbs_id)
        if pbs:
            new_hashes[fm_id] = compute_fm_hash(project, fm_id)
    return new_hashes


@dataclass(frozen=True)
class IncrementalRunResult:
    """Resultaat van :func:`run_incremental_analysis`."""

    fm_results: dict[str, FMResult]
    pbs_results: dict[str, PBSResult]
    cache_only: bool
    """Alleen cache gelezen; geen ``run_analytical`` en geen ``save_cache``."""
    affected_fm_ids: list[str]
    """FM-id's die opnieuw zijn berekend; leeg bij cache-only of volledige run."""
    recalculated_fm_count: int
    """Aantal FM's dat in deze run door de engine is herberekend (0 bij cache-only)."""
    parallel_retried_sequential: bool = False
    """True als parallelle ``run_analytical`` faalde en sequentieel is herhaald."""


def run_incremental_analysis(
    project: RCMProject,
    project_path: str | Path,
    *,
    full_recompute: bool = False,
    parallel: bool = True,
    before_analytical: Callable[[list[str]], None] | None = None,
    scenario_key: str | None = None,
) -> IncrementalRunResult:
    """Laad cache, bepaal delta, voer zo nodig ``run_analytical`` uit, werk cache bij.

    Caller moet eerst structurele validatie hebben gedaan (bijv. ``validate_project``).

    Bij ``full_recompute=True`` wordt de volledige faalwijzen-set herberekend en wordt
    de cache overschreven. Bij incrementele modus zonder gewijzigde FM's worden
    resultaten uit de cache gecombineerd tot FM- en PBS-resultaten (geen schrijven naar
    cachebestand).
    """
    path = Path(project_path)
    total_fm = len(project.faalwijzes)

    if full_recompute:
        if parallel:
            _limit_blas_threads_for_parallel()
        retried = False
        try:
            fm_results, pbs_results = run_analytical(project, fm_ids=None, parallel=parallel)
        except BrokenProcessPool:
            if parallel:
                retried = True
                fm_results, pbs_results = run_analytical(project, fm_ids=None, parallel=False)
            else:
                raise
        new_hashes = _build_fm_hashes(project)
        save_cache(path, new_hashes, fm_results, project, scenario_key=scenario_key)
        return IncrementalRunResult(
            fm_results=fm_results,
            pbs_results=pbs_results,
            cache_only=False,
            affected_fm_ids=[],
            recalculated_fm_count=total_fm,
            parallel_retried_sequential=retried,
        )

    snap = load_cache_snapshot(project, path, scenario_key=scenario_key)
    cached_hashes, cached_raw = snap.hashes, snap.raw_results
    affected = find_affected_fms(project, cached_hashes)

    if not affected:
        fm_results = {fid: FMResult.from_dict(raw) for fid, raw in cached_raw.items()}
        pbs_results = compute_pbs_results(project, fm_results)
        return IncrementalRunResult(
            fm_results=fm_results,
            pbs_results=pbs_results,
            cache_only=True,
            affected_fm_ids=[],
            recalculated_fm_count=0,
            parallel_retried_sequential=False,
        )

    if before_analytical is not None:
        before_analytical(affected)

    if parallel:
        _limit_blas_threads_for_parallel()
    retried = False
    try:
        fm_results, _ = run_analytical(project, fm_ids=affected, parallel=parallel)
    except BrokenProcessPool:
        if parallel:
            retried = True
            fm_results, _ = run_analytical(project, fm_ids=affected, parallel=False)
        else:
            raise

    fm_results = merge_results(fm_results, cached_raw, affected)
    pbs_results = compute_pbs_results(project, fm_results)

    new_hashes = _build_fm_hashes(project)
    save_cache(path, new_hashes, fm_results, project, scenario_key=scenario_key)

    return IncrementalRunResult(
        fm_results=fm_results,
        pbs_results=pbs_results,
        cache_only=False,
        affected_fm_ids=list(affected),
        recalculated_fm_count=len(affected),
        parallel_retried_sequential=retried,
    )
