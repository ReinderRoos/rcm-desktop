"""Memoization voor werkruimte-presentatie (slice 24 issue 07).

Qt-vrije cache van adapter-builders per (slot, scope, modus).
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from rcm_desktop.adapter.ltap_view_cache import invalidate_ltap_view_cache

SLOT_CURRENT = "CURRENT"
SLOT_A = "A"
SLOT_B = "B"
SLOT_CM = "CM"
SLOT_PM = "PM"

T = TypeVar("T")

CacheKey = tuple[str, str | None, str]


class WorkspaceRenderIndex:
    """Cache presentatie-input per slot, PBS-scope en actieve modus."""

    def __init__(self) -> None:
        self._cache: dict[CacheKey, object] = {}

    def get_or_build(
        self,
        slot_key: str,
        scope_id: str | None,
        modus: str,
        builder: Callable[[], T],
    ) -> T:
        key: CacheKey = (slot_key, scope_id, modus)
        cached = self._cache.get(key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        value = builder()
        self._cache[key] = value
        return value

    def on_slot_updated(self, slot_key: str) -> None:
        drop = [k for k in self._cache if k[0] == slot_key]
        for key in drop:
            del self._cache[key]

    def on_project_changed(self) -> None:
        self._cache.clear()
        invalidate_ltap_view_cache()

    def on_workspace_state_reset(self) -> None:
        self._cache.clear()
