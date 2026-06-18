"""Input/Output-zijde + view-tabs in navigatierail (slice 79 / 107)."""

from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtWidgets import (
    QButtonGroup,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from rcm_desktop.adapter.results_workspace_state import ResultsWorkspaceState
from rcm_desktop.adapter.workspace_view_registry import (
    SIDE_OUTPUT,
    WORKSPACE_NAV_RAIL_WIDTH_PX,
    WORKSPACE_SIDES,
    WORKSPACE_VIEW_REGISTRY,
    enabled_views_for_side,
    rail_label_for_view,
    view_by_id,
)
from rcm_desktop.theme.rcm2_theme import enable_stylesheet_background


@dataclass(frozen=True)
class ViewTabItem:
    view_id: str
    label: str
    rail_label: str
    enabled: bool


@dataclass
class WorkspaceNavigationPanel:
    widget: QWidget
    side_button_group: QButtonGroup
    side_buttons: dict[str, QToolButton]
    view_tab_group: QButtonGroup
    view_tab_buttons: dict[str, QToolButton] = field(default_factory=dict)
    view_tabs_container: QWidget | None = None
    _view_tabs_layout: QVBoxLayout | None = None


def build_workspace_navigation_panel(
    workspace_state: ResultsWorkspaceState,
) -> WorkspaceNavigationPanel:
    widget = QWidget()
    widget.setObjectName("WorkspaceNavRail")
    widget.setFixedWidth(WORKSPACE_NAV_RAIL_WIDTH_PX)
    widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
    enable_stylesheet_background(widget)
    column = QVBoxLayout(widget)
    column.setContentsMargins(8, 8, 8, 8)
    column.setSpacing(6)

    side_button_group = QButtonGroup(widget)
    side_button_group.setExclusive(True)
    side_buttons: dict[str, QToolButton] = {}
    for side_entry in WORKSPACE_SIDES:
        button = QToolButton()
        button.setObjectName("WorkspaceSideTab")
        button.setText(side_entry.label)
        button.setCheckable(True)
        button.setToolTip(side_entry.shortcut)
        button.clicked.connect(
            lambda _checked=False, side=side_entry.side_id: workspace_state.set_workspace_side(
                side
            )
        )
        side_button_group.addButton(button)
        side_buttons[side_entry.side_id] = button
        column.addWidget(button)

    column.addSpacing(8)

    view_tabs_container = QWidget()
    view_tabs_container.setObjectName("WorkspaceViewTabs")
    view_tabs_layout = QVBoxLayout(view_tabs_container)
    view_tabs_layout.setContentsMargins(0, 0, 0, 0)
    view_tabs_layout.setSpacing(2)
    column.addWidget(view_tabs_container, stretch=1)

    view_tab_group = QButtonGroup(widget)
    view_tab_group.setExclusive(True)

    panel = WorkspaceNavigationPanel(
        widget=widget,
        side_button_group=side_button_group,
        side_buttons=side_buttons,
        view_tab_group=view_tab_group,
        view_tabs_container=view_tabs_container,
        _view_tabs_layout=view_tabs_layout,
    )
    _rebuild_view_tabs(
        panel,
        workspace_state=workspace_state,
        dropdown_items=tuple(
            ViewTabItem(
                view_id=entry.view_id,
                label=entry.label,
                rail_label=rail_label_for_view(entry),
                enabled=entry.enabled,
            )
            for entry in enabled_views_for_side(WORKSPACE_VIEW_REGISTRY, SIDE_OUTPUT)
        ),
    )
    side_buttons[SIDE_OUTPUT].setChecked(True)

    return panel


def _on_view_tab_clicked(view_id: str, workspace_state: ResultsWorkspaceState) -> None:
    try:
        workspace_state.set_active_view(view_id)
    except ValueError:
        return


def _rebuild_view_tabs(
    panel: WorkspaceNavigationPanel,
    *,
    workspace_state: ResultsWorkspaceState,
    dropdown_items: tuple[object, ...],
) -> None:
    layout = panel._view_tabs_layout
    if layout is None:
        return
    for button in panel.view_tab_buttons.values():
        panel.view_tab_group.removeButton(button)
        button.deleteLater()
    panel.view_tab_buttons.clear()
    while layout.count():
        item = layout.takeAt(0)
        child = item.widget()
        if child is not None:
            child.deleteLater()

    for item in dropdown_items:
        view_id = getattr(item, "view_id")
        rail_label = getattr(item, "rail_label", None) or getattr(item, "label")
        entry = view_by_id(WORKSPACE_VIEW_REGISTRY, view_id)
        tooltip = entry.label if entry is not None else rail_label
        button = QToolButton()
        button.setObjectName("WorkspaceViewTab")
        button.setText(rail_label)
        button.setToolTip(tooltip)
        button.setCheckable(True)
        button.setEnabled(getattr(item, "enabled"))
        button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        button.clicked.connect(
            lambda _checked=False, vid=view_id: _on_view_tab_clicked(vid, workspace_state)
        )
        panel.view_tab_group.addButton(button)
        panel.view_tab_buttons[view_id] = button
        layout.addWidget(button)
    layout.addStretch(1)


def apply_workspace_navigation_plan(
    panel: WorkspaceNavigationPanel,
    *,
    workspace_state: ResultsWorkspaceState,
    workspace_side: str,
    active_view_id: str,
    dropdown_items: tuple[object, ...],
) -> None:
    for side_id, button in panel.side_buttons.items():
        checked = side_id == workspace_side
        if button.isChecked() != checked:
            button.setChecked(checked)

    expected_ids = [getattr(item, "view_id") for item in dropdown_items]
    current_ids = list(panel.view_tab_buttons.keys())
    if current_ids != expected_ids:
        _rebuild_view_tabs(
            panel,
            workspace_state=workspace_state,
            dropdown_items=dropdown_items,
        )
    else:
        for item in dropdown_items:
            view_id = getattr(item, "view_id")
            button = panel.view_tab_buttons.get(view_id)
            if button is not None:
                enabled = getattr(item, "enabled")
                rail_label = getattr(item, "rail_label", None) or getattr(item, "label")
                if button.isEnabled() != enabled:
                    button.setEnabled(enabled)
                if button.text() != rail_label:
                    button.setText(rail_label)

    active_button = panel.view_tab_buttons.get(active_view_id)
    if active_button is not None and not active_button.isChecked():
        blocker = active_button.blockSignals(True)
        active_button.setChecked(True)
        active_button.blockSignals(blocker)
