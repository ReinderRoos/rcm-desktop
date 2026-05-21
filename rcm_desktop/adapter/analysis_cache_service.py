"""FM-cache hydratie na valideren (slice 26, issue 03).

Qt-vrije module: leest `.rcm.cache.json` via de kern-cache-API en bouwt een
`RunResult` wanneer de globale digest én alle FM-hashes vertrouwd zijn.
"""
from __future__ import annotations

from pathlib import Path

from rcm_core.cache import find_affected_fms, load_cache_snapshot
from rcm_core.engine import compute_pbs_results
from rcm_core.models import FMResult, RCMProject

from rcm_desktop.adapter.result_view_service import build_pbs_rows, build_rows
from rcm_desktop.adapter.run_service import RunMetrics, RunResult


def fm_cache_available(project: RCMProject, project_path: str | Path) -> bool:
    """True wanneer een vertrouwde FM-cache voor het project beschikbaar is."""
    snap = load_cache_snapshot(project, Path(project_path))
    if not snap.global_layer_trusted or not snap.raw_results:
        return False
    return not find_affected_fms(project, snap.hashes)


def hydrate_run_from_cache(
    project: RCMProject,
    project_path: str | Path,
) -> RunResult | None:
    """Bouw `RunResult` uit cache zonder de analytische motor te draaien."""
    snap = load_cache_snapshot(project, Path(project_path))
    if not snap.global_layer_trusted or not snap.raw_results:
        return None
    if find_affected_fms(project, snap.hashes):
        return None

    fm_results = {fid: FMResult.from_dict(raw) for fid, raw in snap.raw_results.items()}
    if not fm_results:
        return None

    pbs_results = compute_pbs_results(project, fm_results)
    fm_list = list(fm_results.values())
    metrics = RunMetrics(
        fm_result_count=len(fm_list),
        total_lifecycle_faalmomenten=sum(item.expected_failures for item in fm_list),
        total_cost_eur=sum(item.total_cost_eur for item in fm_list),
        total_downtime_hr=sum(
            item.expected_total_downtime_hr + item.expected_pm_downtime_hr for item in fm_list
        ),
        lifecycle_years=float(project.config.lifecycle_years),
        total_risk_contribution=sum(item.risk_contribution for item in fm_list),
    )
    return RunResult(
        status="done",
        summary=f"Geladen uit cache ({metrics.fm_result_count} FM-resultaten).",
        metrics=metrics,
        rows=build_rows(project, fm_list),
        pbs_rows=build_pbs_rows(project, pbs_results),
        fm_core_results=tuple(fm_list),
    )
