"""QMenuBar-binding voor de resultatenwerkruimte (slice 76 issue 02)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow

from rcm_desktop.adapter.workspace_menu_spec import WORKSPACE_MENU_SPEC
from rcm_desktop.adapter.workspace_view_menu import workspace_view_menu_groups
from rcm_desktop.adapter.workspace_view_registry import WORKSPACE_VIEW_REGISTRY, view_by_id


@dataclass(frozen=True)
class WorkspaceMenuHandlers:
    open_project: Callable[[], None]
    open_rcm_cost: Callable[[], None]
    export_rcm_cost: Callable[[], None]
    quit: Callable[[], None]
    set_pbs_sidebar_visible: Callable[[bool], None]
    set_kpi_overview_visible: Callable[[bool], None]
    set_fm_column_crop: Callable[[bool], None]
    toggle_lcc_whatif: Callable[[], None]
    run_compare_slot_a: Callable[[], None]
    run_compare_slot_b: Callable[[], None]
    set_compare_scenario_cm: Callable[[], None]
    set_compare_scenario_pm: Callable[[], None]
    revalidate_input: Callable[[], None]
    open_faalwijzen_grid: Callable[[], None]
    open_model_settings: Callable[[], None]
    open_report_generation: Callable[[], None]
    pbs_select_prev_sibling: Callable[[], None]
    pbs_select_next_sibling: Callable[[], None]
    pbs_select_parent: Callable[[], None]
    pbs_select_first_child: Callable[[], None]
    pbs_move_up: Callable[[], None]
    pbs_move_down: Callable[[], None]
    set_workspace_side: Callable[[str], None]
    set_active_view: Callable[[str], None]


@dataclass
class WorkspaceMenuBinding:
    actions_by_id: dict[str, QAction]


def build_workspace_menu_bar(
    window: QMainWindow,
    handlers: WorkspaceMenuHandlers,
    *,
    include_column_crop: bool = True,
) -> WorkspaceMenuBinding:
    menubar = window.menuBar()
    actions_by_id: dict[str, QAction] = {}

    for section in WORKSPACE_MENU_SPEC:
        menu = menubar.addMenu(section.label)
        for item in section.items:
            if item.action_id == "view.column_crop" and not include_column_crop:
                continue
            action = _make_action(window, item.label, item.shortcut, item.checkable)
            _connect_action(action, item.action_id, handlers)
            menu.addAction(action)
            actions_by_id[item.action_id] = action

        if section.menu_id == "view":
            menu.addSeparator()
            for group in workspace_view_menu_groups():
                if group.group_id == "view_sides":
                    for item in group.items:
                        action = _make_action(
                            window, item.label, item.shortcut, item.checkable
                        )
                        _connect_action(action, item.action_id, handlers)
                        menu.addAction(action)
                        actions_by_id[item.action_id] = action
                    continue
                submenu = menu.addMenu(group.label)
                for item in group.items:
                    action = _make_action(
                        window, item.label, item.shortcut, item.checkable
                    )
                    action.setEnabled(item.enabled)
                    _connect_action(action, item.action_id, handlers)
                    submenu.addAction(action)
                    actions_by_id[item.action_id] = action

    return WorkspaceMenuBinding(actions_by_id=actions_by_id)


def sync_workspace_menu_check_states(
    binding: WorkspaceMenuBinding,
    *,
    pbs_sidebar_visible: bool,
    kpi_overview_visible: bool,
    fm_column_crop_checked: bool | None = None,
    workspace_side: str | None = None,
    active_view_id: str | None = None,
) -> None:
    _set_checked(binding.actions_by_id.get("view.pbs_tree_visible"), pbs_sidebar_visible)
    _set_checked(
        binding.actions_by_id.get("view.kpi_overview_visible"),
        kpi_overview_visible,
    )
    if fm_column_crop_checked is not None:
        _set_checked(
            binding.actions_by_id.get("view.column_crop"),
            fm_column_crop_checked,
        )
    if workspace_side is not None:
        _set_checked(binding.actions_by_id.get("view.side.input"), workspace_side == "input")
        _set_checked(binding.actions_by_id.get("view.side.output"), workspace_side == "output")
    if active_view_id is not None and workspace_side is not None:
        for action_id, action in binding.actions_by_id.items():
            if not action_id.startswith("view.") or action_id.startswith("view.side."):
                continue
            view_id = action_id.removeprefix("view.")
            entry = view_by_id(WORKSPACE_VIEW_REGISTRY, view_id)
            if entry is None:
                continue
            on_active_side = entry.side == workspace_side
            action.setEnabled(entry.enabled and on_active_side)
            _set_checked(action, view_id == active_view_id)


def _make_action(
    window: QMainWindow,
    label: str,
    shortcut: str | None,
    checkable: bool,
) -> QAction:
    action = QAction(label, window)
    if shortcut is not None:
        action.setShortcut(QKeySequence(shortcut))
    if checkable:
        action.setCheckable(True)
    return action


def _set_checked(action: QAction | None, checked: bool) -> None:
    if action is None:
        return
    blocker = action.blockSignals(True)
    action.setChecked(checked)
    action.blockSignals(blocker)


def _connect_action(
    action: QAction,
    action_id: str,
    handlers: WorkspaceMenuHandlers,
) -> None:
    if action_id == "file.open_project":
        action.triggered.connect(handlers.open_project)
        return
    if action_id == "file.open_rcm_cost":
        action.triggered.connect(handlers.open_rcm_cost)
        return
    if action_id == "file.export_rcm_cost":
        action.triggered.connect(handlers.export_rcm_cost)
        return
    if action_id == "file.quit":
        action.triggered.connect(handlers.quit)
        return
    if action_id == "view.pbs_tree_visible":
        action.toggled.connect(handlers.set_pbs_sidebar_visible)
        return
    if action_id == "view.kpi_overview_visible":
        action.toggled.connect(handlers.set_kpi_overview_visible)
        return
    if action_id == "view.column_crop":
        action.toggled.connect(handlers.set_fm_column_crop)
        return
    if action_id == "run.toggle_whatif":
        action.triggered.connect(handlers.toggle_lcc_whatif)
        return
    if action_id == "run.slot_a":
        action.triggered.connect(handlers.run_compare_slot_a)
        return
    if action_id == "run.slot_b":
        action.triggered.connect(handlers.run_compare_slot_b)
        return
    if action_id == "run.scenario_cm":
        action.triggered.connect(handlers.set_compare_scenario_cm)
        return
    if action_id == "run.scenario_pm":
        action.triggered.connect(handlers.set_compare_scenario_pm)
        return
    if action_id == "analysis.revalidate_input":
        action.triggered.connect(handlers.revalidate_input)
        return
    if action_id == "analysis.faalwijzen_grid":
        action.triggered.connect(handlers.open_faalwijzen_grid)
        return
    if action_id == "analysis.model_settings":
        action.triggered.connect(handlers.open_model_settings)
        return
    if action_id == "analysis.generate_report":
        action.triggered.connect(handlers.open_report_generation)
        return
    if action_id == "view.pbs_select_prev_sibling":
        action.triggered.connect(handlers.pbs_select_prev_sibling)
        return
    if action_id == "view.pbs_select_next_sibling":
        action.triggered.connect(handlers.pbs_select_next_sibling)
        return
    if action_id == "view.pbs_select_parent":
        action.triggered.connect(handlers.pbs_select_parent)
        return
    if action_id == "view.pbs_select_first_child":
        action.triggered.connect(handlers.pbs_select_first_child)
        return
    if action_id == "view.pbs_move_up":
        action.triggered.connect(handlers.pbs_move_up)
        return
    if action_id == "view.pbs_move_down":
        action.triggered.connect(handlers.pbs_move_down)
        return
    if action_id == "view.side.input":
        action.triggered.connect(lambda _checked=False: handlers.set_workspace_side("input"))
        return
    if action_id == "view.side.output":
        action.triggered.connect(lambda _checked=False: handlers.set_workspace_side("output"))
        return
    if action_id.startswith("view."):
        view_id = action_id.removeprefix("view.")
        action.triggered.connect(
            lambda _checked=False, vid=view_id: handlers.set_active_view(vid)
        )
        return
    raise ValueError(f"unknown menu action_id: {action_id}")
