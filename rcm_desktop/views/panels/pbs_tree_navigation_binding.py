"""PBS-boom navigatie en reorder (slice 86 + panel-extractie)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QModelIndex

from rcm_desktop.adapter.pbs_order_service import swap_pbs_sibling_order
from rcm_desktop.adapter.pbs_tree_navigation_service import pbs_id_for_navigation
from rcm_desktop.adapter.rcm_navigation_tree_builder import NavigationNodeKind, RcmNavigationNode


def pbs_tree_has_focus(window: Any) -> bool:
    focus = window.focusWidget()
    return focus is not None and (
        focus is window.pbs_tree_view or window.pbs_tree_view.isAncestorOf(focus)
    )


def current_pbs_scope_id(window: Any) -> str | None:
    source_model = window._pbs_source_model
    if source_model is None:
        return None
    current = window.pbs_tree_view.currentIndex()
    if not current.isValid():
        return None
    source_index = window.pbs_proxy.mapToSource(current)
    if not source_index.isValid():
        return None
    return window._pbs_scope_from_tree_index(source_model, source_index)


def select_pbs_id_in_tree(window: Any, pbs_id: str) -> None:
    source_model = window._pbs_source_model
    if source_model is None:
        return
    idx = find_pbs_index(window, source_model, QModelIndex(), pbs_id)
    if idx is not None and idx.isValid():
        proxy_idx = window.pbs_proxy.mapFromSource(idx)
        window.pbs_tree_view.setCurrentIndex(proxy_idx)


def find_pbs_index(window: Any, model, parent, pbs_id: str):
    rows = model.rowCount(parent)
    for row in range(rows):
        idx = model.index(row, 0, parent)
        node = idx.internalPointer()
        if isinstance(node, RcmNavigationNode) and node.kind == NavigationNodeKind.PBS:
            if node.node_id == pbs_id:
                return idx
        child = find_pbs_index(window, model, idx, pbs_id)
        if child is not None:
            return child
    return None


def pbs_tree_navigate(window: Any, action: str) -> None:
    if not pbs_tree_has_focus(window):
        return
    project = window._state.last_project
    if project is None:
        return
    current = current_pbs_scope_id(window)
    if current is None:
        return
    target = pbs_id_for_navigation(project, current, action)
    if target is None:
        return
    select_pbs_id_in_tree(window, target)


def pbs_tree_reorder(window: Any, direction: str) -> None:
    if not pbs_tree_has_focus(window):
        return
    project = window._state.last_project
    if project is None:
        return
    current = current_pbs_scope_id(window)
    if current is None:
        return
    updated, changed = swap_pbs_sibling_order(
        project, current, direction="up" if direction == "up" else "down"
    )
    if not changed:
        return
    path = window._state.loaded_project.path if window._state.loaded_project else None
    window._state.set_last_project(updated, path=path, preserve_workspace_ui=True)
