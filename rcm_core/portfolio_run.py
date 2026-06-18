"""Portfolio-run: submodel cache-partitionering (ADR-0009, slice 64 issue 02)."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import TypeVar

from rcm_core.cache import load_cache
from rcm_core.models import FMResult, RCMProject
from rcm_core.portfolio_manifest import PortfolioManifest


def submodel_cache_key(source_id: str) -> str:
    """Scenario-key voor per-submodel FM-cache."""
    safe = source_id.strip().replace(" ", "-")
    return f"submodel.{safe}"


def _netwerkschakel_for_source(
    manifest: PortfolioManifest,
    source_id: str,
) -> str | None:
    for entry in manifest.sources:
        if entry.source_id == source_id:
            return entry.netwerkschakel_label
    return None


def fm_ids_for_source(
    project: RCMProject,
    manifest: PortfolioManifest,
    source_id: str,
) -> list[str]:
    """Prefixed FM-id's die bij één bron horen."""
    label = _netwerkschakel_for_source(manifest, source_id)
    if label is None:
        return []
    prefix = f"{label}::"
    return sorted(fm_id for fm_id in project.faalwijzes if fm_id.startswith(prefix))


_TDictVal = TypeVar("_TDictVal")


def _filter_prefixed(items: dict[str, _TDictVal], prefix: str) -> dict[str, _TDictVal]:
    needle = f"{prefix}::"
    return {k: v for k, v in items.items() if k.startswith(needle)}


def extract_submodel_project(
    portfolio: RCMProject,
    manifest: PortfolioManifest,
    source_id: str,
) -> RCMProject | None:
    """Subset van portfolio dat één netwerkschakel representeert (voor aparte run)."""
    label = _netwerkschakel_for_source(manifest, source_id)
    if label is None:
        return None

    entry = next(s for s in manifest.sources if s.source_id == source_id)
    sub = RCMProject(
        config=deepcopy(portfolio.config),
        projectnaam=entry.netwerkschakel_label,
    )
    sub.config.lifecycle_years = entry.lifecycle_years or sub.config.lifecycle_years
    if entry.modeljaar is not None:
        sub.config.modeljaar = entry.modeljaar

    sub.pbs_items = _filter_prefixed(portfolio.pbs_items, label)
    sub.functies = _filter_prefixed(portfolio.functies, label)
    sub.faalwijzes = _filter_prefixed(portfolio.faalwijzes, label)
    sub.pm_tasks = _filter_prefixed(portfolio.pm_tasks, label)
    sub.task_groups = _filter_prefixed(portfolio.task_groups, label)
    sub.effect_klassen = _filter_prefixed(portfolio.effect_klassen, label)
    sub.fm_effect_links = _filter_prefixed(portfolio.fm_effect_links, label)
    sub.pm_effect_links = _filter_prefixed(portfolio.pm_effect_links, label)
    sub.bibliotheek = _filter_prefixed(portfolio.bibliotheek, label)
    return sub


def merge_submodel_fm_results(
    portfolio_path: Path,
    manifest: PortfolioManifest,
) -> dict[str, FMResult]:
    """Combineer FM-resultaten uit alle submodel-cache-partities."""
    merged: dict[str, FMResult] = {}
    for source in manifest.sources:
        key = submodel_cache_key(source.source_id)
        _, raw = load_cache(portfolio_path, scenario_key=key)
        for fm_id, payload in raw.items():
            merged[fm_id] = FMResult.from_dict(payload)
    return merged
