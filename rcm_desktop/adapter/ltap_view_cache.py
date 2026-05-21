"""Memoization voor LTAP-view builds (slice 36 issue 02)."""
from __future__ import annotations

from rcm_core.models import RCMProject

from rcm_desktop.adapter.ltap_service import LTAPView, build_ltap_view

CacheKey = tuple[
    tuple[tuple[str, float], ...],
    tuple[str, ...],
    tuple[str, ...] | None,
    str | None,
]


def _cache_key(
    *,
    overlay_anchor_years: dict[str, float] | None,
    disabled_pm_ids: frozenset[str] | None,
    fm_pbs_ids: frozenset[str] | None,
    taak_type_filter: str | None,
) -> CacheKey:
    anchors = tuple(sorted((overlay_anchor_years or {}).items()))
    disabled = tuple(sorted(disabled_pm_ids or ()))
    scope = tuple(sorted(fm_pbs_ids)) if fm_pbs_ids is not None else None
    return (anchors, disabled, scope, taak_type_filter)


class LTAPViewCache:
    """Session-scoped LTAP memoization; invalidate bij project-wissel."""

    def __init__(self) -> None:
        self._views: dict[CacheKey, LTAPView] = {}
        self._project_token: int | None = None

    def clear_for_project_change(self) -> None:
        self._views.clear()
        self._project_token = None

    def get(
        self,
        project: RCMProject,
        *,
        overlay_anchor_years: dict[str, float] | None = None,
        taak_type_filter: str | None = None,
        disabled_pm_ids: frozenset[str] | None = None,
        fm_pbs_ids: frozenset[str] | None = None,
    ) -> LTAPView:
        token = id(project)
        if self._project_token != token:
            self._views.clear()
            self._project_token = token
        key = _cache_key(
            overlay_anchor_years=overlay_anchor_years,
            disabled_pm_ids=disabled_pm_ids,
            fm_pbs_ids=fm_pbs_ids,
            taak_type_filter=taak_type_filter,
        )
        cached = self._views.get(key)
        if cached is not None:
            return cached
        view = build_ltap_view(
            project,
            overlay_anchor_years=overlay_anchor_years,
            taak_type_filter=taak_type_filter,
            disabled_pm_ids=disabled_pm_ids,
            fm_pbs_ids=fm_pbs_ids,
        )
        self._views[key] = view
        return view


_shared_cache = LTAPViewCache()


def get_ltap_view(
    project: RCMProject,
    *,
    overlay_anchor_years: dict[str, float] | None = None,
    taak_type_filter: str | None = None,
    disabled_pm_ids: frozenset[str] | None = None,
    fm_pbs_ids: frozenset[str] | None = None,
) -> LTAPView:
    """Cached LTAP-view voor presentatie hot paths."""
    return _shared_cache.get(
        project,
        overlay_anchor_years=overlay_anchor_years,
        taak_type_filter=taak_type_filter,
        disabled_pm_ids=disabled_pm_ids,
        fm_pbs_ids=fm_pbs_ids,
    )


def invalidate_ltap_view_cache() -> None:
    """Roep aan bij project-wissel in UI."""
    _shared_cache.clear_for_project_change()
