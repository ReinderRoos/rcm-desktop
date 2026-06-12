"""Beeld-menu-items gegenereerd uit de view-registry (slice 79 issue 02)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop import messages
from rcm_desktop.adapter.workspace_view_registry import (
    SIDE_INPUT,
    SIDE_OUTPUT,
    WORKSPACE_SIDES,
    WORKSPACE_VIEW_REGISTRY,
    views_for_side,
)


@dataclass(frozen=True)
class WorkspaceViewMenuItem:
    action_id: str
    label: str
    shortcut: str | None
    checkable: bool
    view_id: str | None = None
    side: str | None = None
    enabled: bool = True


@dataclass(frozen=True)
class WorkspaceViewMenuGroup:
    group_id: str
    label: str
    items: tuple[WorkspaceViewMenuItem, ...]


def workspace_view_menu_groups() -> tuple[WorkspaceViewMenuGroup, ...]:
    return (
        WorkspaceViewMenuGroup(
            group_id="view_sides",
            label=messages.WORKSPACE_MENU_VIEW,
            items=tuple(
                WorkspaceViewMenuItem(
                    action_id=f"view.side.{side.side_id}",
                    label=side.label,
                    shortcut=side.shortcut,
                    checkable=True,
                    side=side.side_id,
                )
                for side in WORKSPACE_SIDES
            ),
        ),
        WorkspaceViewMenuGroup(
            group_id="view_input",
            label=messages.WORKSPACE_SIDE_INPUT,
            items=_view_items_for_side(SIDE_INPUT),
        ),
        WorkspaceViewMenuGroup(
            group_id="view_output",
            label=messages.WORKSPACE_SIDE_OUTPUT,
            items=_view_items_for_side(SIDE_OUTPUT),
        ),
    )


def _view_items_for_side(side: str) -> tuple[WorkspaceViewMenuItem, ...]:
    return tuple(
        WorkspaceViewMenuItem(
            action_id=f"view.{entry.view_id}",
            label=entry.label,
            shortcut=entry.shortcut,
            checkable=True,
            view_id=entry.view_id,
            side=entry.side,
            enabled=entry.enabled,
        )
        for entry in views_for_side(WORKSPACE_VIEW_REGISTRY, side)
    )


def all_view_menu_shortcuts() -> set[str]:
    shortcuts: set[str] = set()
    for group in workspace_view_menu_groups():
        for item in group.items:
            if item.shortcut is not None:
                shortcuts.add(item.shortcut)
    return shortcuts
