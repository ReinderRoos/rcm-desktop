"""Compat: dirty guard verhuisd naar views (slice 46-08)."""

from __future__ import annotations

from rcm_desktop.views.grid_dirty_guard import (
    GridDirtyResolution,
    resolve_grid_dirty_before_editor,
)

__all__ = ["GridDirtyResolution", "resolve_grid_dirty_before_editor"]
