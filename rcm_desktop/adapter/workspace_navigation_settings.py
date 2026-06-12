"""QSettings-seam voor werkruimte-navigatie (slice 79 issue 03)."""

from __future__ import annotations

from typing import Protocol

from rcm_desktop.adapter.workspace_view_registry import (
    DEFAULT_VIEW_BY_SIDE,
    SIDE_INPUT,
    SIDE_OUTPUT,
    WORKSPACE_VIEW_REGISTRY,
    view_by_id,
)

WORKSPACE_SIDE_SETTINGS_KEY = "workspace/navigation/side"
WORKSPACE_STICKY_VIEW_SETTINGS_PREFIX = "workspace/navigation/sticky/"


class _SettingsLike(Protocol):
    def value(self, key: str, default: object = ..., type: type | None = None) -> object: ...

    def setValue(self, key: str, value: object) -> None: ...


def _normalize_view_id(view_id: object | None, *, side: str) -> str:
    default = DEFAULT_VIEW_BY_SIDE.get(side, DEFAULT_VIEW_BY_SIDE[SIDE_OUTPUT])
    if not isinstance(view_id, str):
        return default
    entry = view_by_id(WORKSPACE_VIEW_REGISTRY, view_id)
    if entry is None or entry.side != side:
        return default
    return view_id


def read_workspace_navigation(settings: _SettingsLike) -> tuple[str, dict[str, str]]:
    raw_side = settings.value(WORKSPACE_SIDE_SETTINGS_KEY, SIDE_OUTPUT)
    side = raw_side if raw_side in DEFAULT_VIEW_BY_SIDE else SIDE_OUTPUT
    sticky = {
        SIDE_INPUT: _normalize_view_id(
            settings.value(f"{WORKSPACE_STICKY_VIEW_SETTINGS_PREFIX}{SIDE_INPUT}"),
            side=SIDE_INPUT,
        ),
        SIDE_OUTPUT: _normalize_view_id(
            settings.value(f"{WORKSPACE_STICKY_VIEW_SETTINGS_PREFIX}{SIDE_OUTPUT}"),
            side=SIDE_OUTPUT,
        ),
    }
    return side, sticky


def write_workspace_navigation(
    settings: _SettingsLike,
    *,
    workspace_side: str,
    sticky_by_side: dict[str, str],
) -> None:
    settings.setValue(WORKSPACE_SIDE_SETTINGS_KEY, workspace_side)
    for side in (SIDE_INPUT, SIDE_OUTPUT):
        view_id = sticky_by_side.get(side, DEFAULT_VIEW_BY_SIDE[side])
        settings.setValue(f"{WORKSPACE_STICKY_VIEW_SETTINGS_PREFIX}{side}", view_id)
