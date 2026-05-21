"""Presentatie-cache voor projecttotaal-modi (slice 26, lazy slice 37).

Bouwt, serialiseert en laadt projecttotaal-presentaties in `.rcm.cache.json`
onder `presentation`. Slice 37: post-run alleen Bijdragen-blok; LCC via
`WorkspaceRenderIndex` bij modusbezoek.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from rcm_core.cache import compute_global_digest, load_cache_snapshot
from rcm_core.models import RCMProject

from rcm_desktop.adapter.contribution_chart_service import (
    ContributionRow,
    build_contribution_rows,
)
from rcm_desktop.adapter.lcc_chart_service import LCCYearBucket
from rcm_desktop.adapter.pm_chart_service import (
    PMYearRow,
    PM_SUBMODE_AANTAL_UITVOERINGEN,
    PM_SUBMODE_KOSTEN,
)
from rcm_desktop.adapter.results_workspace_state import (
    ContributionPresentation,
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_BIJDRAGEN,
    MODE_LCC,
    SOURCE_PBS,
    normalize_metric,
)
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.unavailability_chart_service import UnavailabilityYearRow

PRESENTATION_CACHE_VERSION = 3
_LEGACY_PRESENTATION_CACHE_VERSION = 2
_DEFAULT_TOP_N = 10


@dataclass(frozen=True)
class PresentationProjectTotal:
    contribution_source: str
    contribution_metric: str
    contribution_top_n: int
    contribution_presentation: ContributionPresentation
    contribution_rows: tuple[ContributionRow, ...]
    built_modi: frozenset[str] = frozenset({MODE_BIJDRAGEN})
    # Legacy v2 velden — alleen gevuld bij load van oudere cache.
    lcc_buckets: tuple[LCCYearBucket, ...] = ()
    unavailability_rows: tuple[UnavailabilityYearRow, ...] = ()
    pm_kosten_rows: tuple[PMYearRow, ...] = ()
    pm_aantal_rows: tuple[PMYearRow, ...] = ()


def _cache_path(project_path: Path) -> Path:
    return project_path.with_suffix("").with_suffix(".rcm.cache.json")


def build_contribution_presentation(
    project: RCMProject,
    run: RunResult,
) -> PresentationProjectTotal:
    """Bouw alleen Bijdragen/Top-10 presentatie (slice 37 default post-run)."""
    default_presentation = ContributionPresentation()
    contrib = build_contribution_rows(
        project,
        run,
        source=SOURCE_PBS,
        metric=METRIC_NIET_BESCHIKBAARHEID,
        top_n=_DEFAULT_TOP_N,
        scope_id=None,
        presentation=default_presentation,
    )
    return PresentationProjectTotal(
        contribution_source=SOURCE_PBS,
        contribution_metric=METRIC_NIET_BESCHIKBAARHEID,
        contribution_top_n=_DEFAULT_TOP_N,
        contribution_presentation=default_presentation,
        contribution_rows=contrib,
        built_modi=frozenset({MODE_BIJDRAGEN}),
    )


def build_project_total_presentation(
    project: RCMProject,
    run: RunResult,
) -> PresentationProjectTotal:
    """Backward-compat API: post-run bouwt alleen contribution (slice 37)."""
    return build_contribution_presentation(project, run)


def _contribution_section_from_dto(dto: PresentationProjectTotal) -> dict[str, Any]:
    return {
        "source": dto.contribution_source,
        "metric": dto.contribution_metric,
        "top_n": dto.contribution_top_n,
        "presentation": _presentation_to_dict(dto.contribution_presentation),
        "rows": [_contrib_row_to_dict(r) for r in dto.contribution_rows],
    }


def presentation_dto_to_dict(dto: PresentationProjectTotal) -> dict[str, Any]:
    return {
        "presentation_cache_version": PRESENTATION_CACHE_VERSION,
        "built_at_digest": "",
        "project_total": {
            "built_modi": sorted(dto.built_modi),
            "contribution": _contribution_section_from_dto(dto),
        },
    }


def _infer_built_modi_from_legacy(pt: dict[str, Any]) -> frozenset[str]:
    modi: set[str] = set()
    contrib = pt.get("contribution") or {}
    if contrib.get("rows"):
        modi.add(MODE_BIJDRAGEN)
    if pt.get("lcc_buckets"):
        modi.add(MODE_LCC)
    if pt.get("unavailability_rows"):
        modi.add("niet_beschikbaarheid")
    pm = pt.get("pm") or {}
    if pm.get("kosten") or pm.get("aantal_uitvoeringen"):
        modi.add("preventief_onderhoud")
    return frozenset(modi)


def _contribution_from_section(contrib: dict[str, Any]) -> tuple[str, str, int, ContributionPresentation, tuple[ContributionRow, ...]]:
    return (
        str(contrib.get("source", SOURCE_PBS)),
        normalize_metric(str(contrib.get("metric", METRIC_NIET_BESCHIKBAARHEID))),
        int(contrib.get("top_n", _DEFAULT_TOP_N)),
        _presentation_from_dict(contrib.get("presentation")),
        tuple(_contrib_row_from_dict(r) for r in contrib.get("rows") or []),
    )


def presentation_dict_to_dto(data: dict[str, Any]) -> PresentationProjectTotal:
    version = data.get("presentation_cache_version")
    pt = data.get("project_total") or {}

    if version == PRESENTATION_CACHE_VERSION:
        contrib = pt.get("contribution") or {}
        source, metric, top_n, presentation, rows = _contribution_from_section(contrib)
        built_raw = pt.get("built_modi") or []
        built_modi = frozenset(str(m) for m in built_raw) if built_raw else frozenset({MODE_BIJDRAGEN})
        return PresentationProjectTotal(
            contribution_source=source,
            contribution_metric=metric,
            contribution_top_n=top_n,
            contribution_presentation=presentation,
            contribution_rows=rows,
            built_modi=built_modi,
        )

    # v2 legacy layout
    pm = pt.get("pm") or {}
    contrib = pt.get("contribution") or {}
    source, metric, top_n, presentation, rows = _contribution_from_section(contrib)
    return PresentationProjectTotal(
        contribution_source=source,
        contribution_metric=metric,
        contribution_top_n=top_n,
        contribution_presentation=presentation,
        contribution_rows=rows,
        built_modi=_infer_built_modi_from_legacy(pt),
        lcc_buckets=tuple(_lcc_bucket_from_dict(b) for b in pt.get("lcc_buckets") or []),
        unavailability_rows=tuple(
            _nb_row_from_dict(r) for r in pt.get("unavailability_rows") or []
        ),
        pm_kosten_rows=tuple(
            _pm_row_from_dict(r) for r in pm.get("kosten") or pm.get(PM_SUBMODE_KOSTEN) or []
        ),
        pm_aantal_rows=tuple(
            _pm_row_from_dict(r)
            for r in pm.get("aantal_uitvoeringen")
            or pm.get(PM_SUBMODE_AANTAL_UITVOERINGEN)
            or []
        ),
    )


def _presentation_block_valid(project: RCMProject, block: dict[str, Any]) -> bool:
    version = block.get("presentation_cache_version")
    if version not in (PRESENTATION_CACHE_VERSION, _LEGACY_PRESENTATION_CACHE_VERSION):
        return False
    digest = block.get("built_at_digest")
    if not isinstance(digest, str) or digest != compute_global_digest(project):
        return False
    pt = block.get("project_total")
    if not isinstance(pt, dict):
        return False
    if version == PRESENTATION_CACHE_VERSION:
        contrib = pt.get("contribution")
        if not isinstance(contrib, dict):
            return False
        rows = contrib.get("rows")
        return isinstance(rows, list)
    # v2: contribution rows required for workspace
    contrib = pt.get("contribution") or {}
    rows = contrib.get("rows")
    return isinstance(rows, list)


def _contribution_block_present(block: dict[str, Any]) -> bool:
    pt = block.get("project_total") or {}
    if block.get("presentation_cache_version") == PRESENTATION_CACHE_VERSION:
        contrib = pt.get("contribution") or {}
        return isinstance(contrib.get("rows"), list)
    contrib = pt.get("contribution") or {}
    return isinstance(contrib.get("rows"), list)


def load_presentation_from_cache(
    project: RCMProject,
    project_path: str | Path,
) -> PresentationProjectTotal | None:
    snap = load_cache_snapshot(project, Path(project_path))
    if not snap.global_layer_trusted:
        return None
    path = _cache_path(Path(project_path))
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    block = data.get("presentation")
    if not isinstance(block, dict) or not _presentation_block_valid(project, block):
        return None
    return presentation_dict_to_dto(block)


def presentation_needs_rebuild(project: RCMProject, project_path: str | Path) -> bool:
    """True als FM-cache vertrouwd is maar contribution-presentatie ontbreekt."""
    return presentation_modus_needs_rebuild(project, project_path, MODE_BIJDRAGEN)


def presentation_modus_needs_rebuild(
    project: RCMProject,
    project_path: str | Path,
    modus: str,
) -> bool:
    """Modus-bewuste rebuild-beslissing (slice 37). LCC gebruikt render_index."""
    if modus == MODE_LCC:
        return False
    if modus != MODE_BIJDRAGEN:
        return False
    snap = load_cache_snapshot(project, Path(project_path))
    if not snap.global_layer_trusted or not snap.raw_results:
        return False
    path = _cache_path(Path(project_path))
    if not path.exists():
        return True
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    block = data.get("presentation")
    if not isinstance(block, dict):
        return True
    if not _presentation_block_valid(project, block):
        return True
    if not _contribution_block_present(block):
        return True
    dto = presentation_dict_to_dto(block)
    return modus not in dto.built_modi


def attach_presentation_to_cache(
    project_path: str | Path,
    project: RCMProject,
    dto: PresentationProjectTotal,
) -> None:
    """Schrijf of merge het `presentation`-blok; behoud FM-cache."""
    path = _cache_path(Path(project_path))
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    existing_block = data.get("presentation")
    merged = dto
    if isinstance(existing_block, dict) and _presentation_block_valid(project, existing_block):
        existing_dto = presentation_dict_to_dto(existing_block)
        merged = replace(
            dto,
            built_modi=frozenset(existing_dto.built_modi | dto.built_modi),
            lcc_buckets=existing_dto.lcc_buckets or dto.lcc_buckets,
            unavailability_rows=existing_dto.unavailability_rows or dto.unavailability_rows,
            pm_kosten_rows=existing_dto.pm_kosten_rows or dto.pm_kosten_rows,
            pm_aantal_rows=existing_dto.pm_aantal_rows or dto.pm_aantal_rows,
        )

    payload = presentation_dto_to_dict(merged)
    payload["built_at_digest"] = compute_global_digest(project)
    data["presentation"] = payload
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def rebuild_presentation_only(
    project: RCMProject,
    project_path: str | Path,
    run: RunResult,
    *,
    modus: str = MODE_BIJDRAGEN,
) -> PresentationProjectTotal | None:
    """Herbouw presentatie en schrijf naar cache zonder FM-motor."""
    if run.status != "done":
        return None
    if modus == MODE_LCC:
        return None
    dto = build_contribution_presentation(project, run)
    attach_presentation_to_cache(project_path, project, dto)
    return dto


def _lcc_bucket_from_dict(raw: dict[str, Any]) -> LCCYearBucket:
    return LCCYearBucket(
        calendar_year=int(raw["calendar_year"]),
        correctief_eur=float(raw["correctief_eur"]),
        preventief_eur=float(raw["preventief_eur"]),
    )


def _nb_row_from_dict(raw: dict[str, Any]) -> UnavailabilityYearRow:
    return UnavailabilityYearRow(
        calendar_year=int(raw["calendar_year"]),
        unavailability_pct=float(raw["unavailability_pct"]),
        downtime_hr=float(raw["downtime_hr"]),
    )


def _pm_row_from_dict(raw: dict[str, Any]) -> PMYearRow:
    return PMYearRow(
        calendar_year=int(raw["calendar_year"]),
        value=float(raw["value"]),
        cumulative=float(raw["cumulative"]),
    )


def _contrib_row_to_dict(r: ContributionRow) -> dict[str, Any]:
    return {
        "category_id": r.category_id,
        "label": r.label,
        "value": r.value,
        "share_pct": r.share_pct,
    }


def _presentation_to_dict(p: ContributionPresentation) -> dict[str, Any]:
    year = p.year_choice
    return {
        "horizon": p.horizon,
        "year_choice": year if year == "average" else int(year),
        "unavailability_display": p.unavailability_display,
    }


def _presentation_from_dict(raw: object) -> ContributionPresentation:
    if not isinstance(raw, dict):
        return ContributionPresentation()
    year_raw = raw.get("year_choice", "average")
    year_choice: str | int = (
        "average" if year_raw == "average" else int(year_raw)
    )
    horizon = raw.get("horizon", "per_year")
    if horizon not in ("lifecycle", "per_year"):
        horizon = "per_year"
    display = raw.get("unavailability_display", "hours")
    if display not in ("hours", "percent"):
        display = "hours"
    return ContributionPresentation(
        horizon=horizon,
        year_choice=year_choice,
        unavailability_display=display,
    )


def _contrib_row_from_dict(raw: dict[str, Any]) -> ContributionRow:
    return ContributionRow(
        category_id=str(raw["category_id"]),
        label=str(raw["label"]),
        value=float(raw["value"]),
        share_pct=float(raw["share_pct"]),
    )
