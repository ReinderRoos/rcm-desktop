"""Presentatie-cache voor projecttotaal-modi (slice 26, Fase B).

Bouwt, serialiseert en laadt vier projecttotaal-presentaties (LCC, NB, PM,
Bijdragen) in `.rcm.cache.json` onder `presentation`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rcm_core.cache import compute_global_digest, load_cache_snapshot
from rcm_core.models import RCMProject

from rcm_desktop.adapter.contribution_chart_service import (
    ContributionRow,
    build_contribution_rows,
)
from rcm_desktop.adapter.lcc_chart_service import (
    LCCYearBucket,
    build_single_run_lcc_input,
)
from rcm_desktop.adapter.pm_chart_service import (
    PMYearRow,
    PM_SUBMODE_AANTAL_UITVOERINGEN,
    PM_SUBMODE_KOSTEN,
    build_pm_chart_input,
)
from rcm_desktop.adapter.results_workspace_state import (
    ContributionPresentation,
    METRIC_NIET_BESCHIKBAARHEID,
    SOURCE_PBS,
    normalize_metric,
)
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.unavailability_chart_service import (
    UnavailabilityYearRow,
    build_unavailability_chart_input,
)

PRESENTATION_CACHE_VERSION = 2
_DEFAULT_TOP_N = 10


@dataclass(frozen=True)
class PresentationProjectTotal:
    lcc_buckets: tuple[LCCYearBucket, ...]
    unavailability_rows: tuple[UnavailabilityYearRow, ...]
    pm_kosten_rows: tuple[PMYearRow, ...]
    pm_aantal_rows: tuple[PMYearRow, ...]
    contribution_source: str
    contribution_metric: str
    contribution_top_n: int
    contribution_presentation: ContributionPresentation
    contribution_rows: tuple[ContributionRow, ...]


def _cache_path(project_path: Path) -> Path:
    return project_path.with_suffix("").with_suffix(".rcm.cache.json")


def build_project_total_presentation(
    project: RCMProject,
    run: RunResult,
) -> PresentationProjectTotal:
    """Bouw alle vier projecttotaal-presentaties voor cache-persistentie."""
    lcc_input = build_single_run_lcc_input(project, run)
    lcc_buckets: tuple[LCCYearBucket, ...] = ()
    if lcc_input is not None and lcc_input.single_curve is not None:
        lcc_buckets = tuple(lcc_input.single_curve.buckets)

    nb_input = build_unavailability_chart_input(project, run, scope_id=None)
    nb_rows = nb_input.rows if nb_input is not None else ()

    pm_kosten = build_pm_chart_input(
        project, run, submode=PM_SUBMODE_KOSTEN, scope_id=None
    )
    pm_aantal = build_pm_chart_input(
        project, run, submode=PM_SUBMODE_AANTAL_UITVOERINGEN, scope_id=None
    )

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
        lcc_buckets=lcc_buckets,
        unavailability_rows=nb_rows,
        pm_kosten_rows=pm_kosten.rows if pm_kosten is not None else (),
        pm_aantal_rows=pm_aantal.rows if pm_aantal is not None else (),
        contribution_source=SOURCE_PBS,
        contribution_metric=METRIC_NIET_BESCHIKBAARHEID,
        contribution_top_n=_DEFAULT_TOP_N,
        contribution_presentation=default_presentation,
        contribution_rows=contrib,
    )


def presentation_dto_to_dict(dto: PresentationProjectTotal) -> dict[str, Any]:
    return {
        "presentation_cache_version": PRESENTATION_CACHE_VERSION,
        "built_at_digest": "",
        "project_total": {
            "lcc_buckets": [_lcc_bucket_to_dict(b) for b in dto.lcc_buckets],
            "unavailability_rows": [_nb_row_to_dict(r) for r in dto.unavailability_rows],
            "pm": {
                PM_SUBMODE_KOSTEN: [_pm_row_to_dict(r) for r in dto.pm_kosten_rows],
                PM_SUBMODE_AANTAL_UITVOERINGEN: [
                    _pm_row_to_dict(r) for r in dto.pm_aantal_rows
                ],
            },
            "contribution": {
                "source": dto.contribution_source,
                "metric": dto.contribution_metric,
                "top_n": dto.contribution_top_n,
                "presentation": _presentation_to_dict(dto.contribution_presentation),
                "rows": [_contrib_row_to_dict(r) for r in dto.contribution_rows],
            },
        },
    }


def presentation_dict_to_dto(data: dict[str, Any]) -> PresentationProjectTotal:
    pt = data.get("project_total") or {}
    pm = pt.get("pm") or {}
    contrib = pt.get("contribution") or {}
    return PresentationProjectTotal(
        lcc_buckets=tuple(_lcc_bucket_from_dict(b) for b in pt.get("lcc_buckets") or []),
        unavailability_rows=tuple(
            _nb_row_from_dict(r) for r in pt.get("unavailability_rows") or []
        ),
        pm_kosten_rows=tuple(
            _pm_row_from_dict(r) for r in pm.get(PM_SUBMODE_KOSTEN) or []
        ),
        pm_aantal_rows=tuple(
            _pm_row_from_dict(r) for r in pm.get(PM_SUBMODE_AANTAL_UITVOERINGEN) or []
        ),
        contribution_source=str(contrib.get("source", SOURCE_PBS)),
        contribution_metric=normalize_metric(
            str(contrib.get("metric", METRIC_NIET_BESCHIKBAARHEID))
        ),
        contribution_top_n=int(contrib.get("top_n", _DEFAULT_TOP_N)),
        contribution_presentation=_presentation_from_dict(
            contrib.get("presentation")
        ),
        contribution_rows=tuple(
            _contrib_row_from_dict(r) for r in contrib.get("rows") or []
        ),
    )


def _presentation_block_valid(project: RCMProject, block: dict[str, Any]) -> bool:
    if block.get("presentation_cache_version") != PRESENTATION_CACHE_VERSION:
        return False
    digest = block.get("built_at_digest")
    if not isinstance(digest, str) or digest != compute_global_digest(project):
        return False
    return isinstance(block.get("project_total"), dict)


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
    """True als FM-cache vertrouwd is maar presentatie ontbreekt of verouderd."""
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
    return not _presentation_block_valid(project, block)


def attach_presentation_to_cache(
    project_path: str | Path,
    project: RCMProject,
    dto: PresentationProjectTotal,
) -> None:
    """Schrijf of vervang het `presentation`-blok; behoud FM-cache."""
    path = _cache_path(Path(project_path))
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    payload = presentation_dto_to_dict(dto)
    payload["built_at_digest"] = compute_global_digest(project)
    data["presentation"] = payload
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def rebuild_presentation_only(
    project: RCMProject,
    project_path: str | Path,
    run: RunResult,
) -> PresentationProjectTotal | None:
    """Herbouw presentatie en schrijf naar cache zonder FM-motor."""
    if run.status != "done":
        return None
    dto = build_project_total_presentation(project, run)
    attach_presentation_to_cache(project_path, project, dto)
    return dto


def _lcc_bucket_to_dict(b: LCCYearBucket) -> dict[str, Any]:
    return {
        "calendar_year": b.calendar_year,
        "correctief_eur": b.correctief_eur,
        "preventief_eur": b.preventief_eur,
    }


def _lcc_bucket_from_dict(raw: dict[str, Any]) -> LCCYearBucket:
    return LCCYearBucket(
        calendar_year=int(raw["calendar_year"]),
        correctief_eur=float(raw["correctief_eur"]),
        preventief_eur=float(raw["preventief_eur"]),
    )


def _nb_row_to_dict(r: UnavailabilityYearRow) -> dict[str, Any]:
    return {
        "calendar_year": r.calendar_year,
        "unavailability_pct": r.unavailability_pct,
        "downtime_hr": r.downtime_hr,
    }


def _nb_row_from_dict(raw: dict[str, Any]) -> UnavailabilityYearRow:
    return UnavailabilityYearRow(
        calendar_year=int(raw["calendar_year"]),
        unavailability_pct=float(raw["unavailability_pct"]),
        downtime_hr=float(raw["downtime_hr"]),
    )


def _pm_row_to_dict(r: PMYearRow) -> dict[str, Any]:
    return {
        "calendar_year": r.calendar_year,
        "value": r.value,
        "cumulative": r.cumulative,
    }


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
