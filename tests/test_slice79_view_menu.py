"""Slice 79 issue 02 — view-menu gegenereerd uit registry."""

from __future__ import annotations

from rcm_desktop.adapter.workspace_view_menu import workspace_view_menu_groups
from rcm_desktop.adapter.workspace_view_registry import SIDE_INPUT, SIDE_OUTPUT


def test_view_menu_groups_cover_all_registry_views() -> None:
    groups = workspace_view_menu_groups()
    view_ids = {
        item.view_id
        for group in groups
        for item in group.items
        if item.view_id is not None
    }
    assert len(view_ids) == 8
    assert "output.top_10" not in view_ids
    assert "input.correctief" in view_ids


def test_view_menu_side_shortcuts() -> None:
    groups = workspace_view_menu_groups()
    side_group = groups[0]
    shortcuts = {item.side: item.shortcut for item in side_group.items}
    assert shortcuts[SIDE_INPUT] == "Ctrl+1"
    assert shortcuts[SIDE_OUTPUT] == "Ctrl+2"
