"""Input/Output-zijde-schakelaar + view-dropdown (slice 79)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QToolButton,
    QWidget,
)

from rcm_desktop import messages
from rcm_desktop.adapter.results_workspace_state import ResultsWorkspaceState
from rcm_desktop.adapter.workspace_view_registry import (
    SIDE_INPUT,
    SIDE_OUTPUT,
    WORKSPACE_SIDES,
    WORKSPACE_VIEW_REGISTRY,
    views_for_side,
)


@dataclass(frozen=True)
class WorkspaceNavigationPanel:
    widget: QWidget
    side_button_group: QButtonGroup
    side_buttons: dict[str, QToolButton]
    view_combo: QComboBox


def build_workspace_navigation_panel(
    workspace_state: ResultsWorkspaceState,
) -> WorkspaceNavigationPanel:
    widget = QWidget()
    row = QHBoxLayout(widget)
    row.setContentsMargins(0, 0, 0, 0)

    side_button_group = QButtonGroup(widget)
    side_button_group.setExclusive(True)
    side_buttons: dict[str, QToolButton] = {}
    for side_entry in WORKSPACE_SIDES:
        button = QToolButton()
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
        row.addWidget(button)

    view_combo = QComboBox()
    view_combo.currentIndexChanged.connect(
        lambda _index: _on_view_combo_changed(view_combo, workspace_state)
    )
    row.addWidget(view_combo, stretch=1)

    _populate_view_combo(view_combo, SIDE_OUTPUT)
    side_buttons[SIDE_OUTPUT].setChecked(True)

    return WorkspaceNavigationPanel(
        widget=widget,
        side_button_group=side_button_group,
        side_buttons=side_buttons,
        view_combo=view_combo,
    )


def _populate_view_combo(combo: QComboBox, side: str) -> None:
    blocker = combo.blockSignals(True)
    combo.clear()
    for entry in views_for_side(WORKSPACE_VIEW_REGISTRY, side):
        combo.addItem(entry.label, userData=entry.view_id)
        model_item = combo.model().item(combo.count() - 1)
        if model_item is not None:
            model_item.setEnabled(entry.enabled)
    combo.blockSignals(blocker)


def _on_view_combo_changed(combo: QComboBox, workspace_state: ResultsWorkspaceState) -> None:
    view_id = combo.currentData()
    if not isinstance(view_id, str):
        return
    try:
        workspace_state.set_active_view(view_id)
    except ValueError:
        snap = workspace_state.snapshot()
        index = combo.findData(snap.active_view_id)
        if index >= 0:
            blocker = combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(blocker)


def apply_workspace_navigation_plan(
    panel: WorkspaceNavigationPanel,
    *,
    workspace_side: str,
    active_view_id: str,
    dropdown_items: tuple[object, ...],
) -> None:
    for side_id, button in panel.side_buttons.items():
        checked = side_id == workspace_side
        if button.isChecked() != checked:
            button.setChecked(checked)

    expected_ids = [getattr(item, "view_id") for item in dropdown_items]
    combo = panel.view_combo
    current_ids = [combo.itemData(i) for i in range(combo.count())]
    if current_ids != expected_ids:
        _populate_view_combo(combo, workspace_side)

    index = combo.findData(active_view_id)
    if index >= 0 and index != combo.currentIndex():
        blocker = combo.blockSignals(True)
        combo.setCurrentIndex(index)
        combo.blockSignals(blocker)

    for row_index, item in enumerate(dropdown_items):
        model_item = combo.model().item(row_index)
        if model_item is not None:
            model_item.setEnabled(getattr(item, "enabled"))
