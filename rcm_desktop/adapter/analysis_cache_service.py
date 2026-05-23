"""FM-cache hydratie — delegeert naar ``run_service.hydrate_run_from_cache``."""
from __future__ import annotations

from pathlib import Path

from rcm_core.cache import find_affected_fms, load_cache_snapshot
from rcm_core.models import RCMProject

from rcm_desktop.adapter.run_service import RunResult, hydrate_run_from_cache as _hydrate


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
    return _hydrate(project, project_path)
