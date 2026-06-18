"""PBS-sidebar voor de resultatenwerkruimte (slice 62 follow-up)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtWidgets import QHeaderView, QLabel, QLineEdit, QTreeView, QVBoxLayout, QWidget

from rcm_desktop import messages


class PBSSidebarFilterProxy(QSortFilterProxyModel):
    """Recursief substring-filter op PBS-id en bouwdeelnaam."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setRecursiveFilteringEnabled(True)
        self._needle = ""

    def set_needle(self, needle: str) -> None:
        self._needle = needle.strip().lower()
        self.invalidate()

    def has_needle(self) -> bool:
        return bool(self._needle)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # noqa: N802
        if not self._needle:
            return True
        model = self.sourceModel()
        if model is None:
            return False
        idx_pbs = model.index(source_row, 0, source_parent)
        idx_bouw = model.index(source_row, 1, source_parent)
        pbs_text = (model.data(idx_pbs, Qt.DisplayRole) or "")
        bouw_text = (model.data(idx_bouw, Qt.DisplayRole) or "")
        return self._needle in str(pbs_text).lower() or self._needle in str(bouw_text).lower()


@dataclass
class PBSSidebarPanel:
    sidebar: QWidget
    filter_input: QLineEdit
    tree_view: QTreeView
    empty_state_label: QLabel
    proxy: PBSSidebarFilterProxy


def build_pbs_sidebar_panel() -> PBSSidebarPanel:
    sidebar = QWidget()
    sidebar_layout = QVBoxLayout(sidebar)
    sidebar_layout.setContentsMargins(0, 0, 0, 0)

    filter_input = QLineEdit()
    filter_input.setPlaceholderText(messages.WORKSPACE_PBS_FILTER_PLACEHOLDER)
    filter_input.setToolTip(messages.WORKSPACE_PBS_FILTER_TOOLTIP)
    sidebar_layout.addWidget(filter_input)

    tree_view = QTreeView()
    tree_view.setSortingEnabled(False)
    tree_view.setAlternatingRowColors(True)
    tree_view.setHeaderHidden(False)
    tree_view.header().setSectionResizeMode(QHeaderView.Interactive)
    tree_view.header().setStretchLastSection(True)
    tree_view.setSelectionBehavior(QTreeView.SelectRows)
    sidebar_layout.addWidget(tree_view, stretch=1)

    empty_state_label = QLabel(messages.WORKSPACE_PBS_EMPTY_STATE)
    empty_state_label.setWordWrap(True)
    empty_state_label.setVisible(False)
    sidebar_layout.addWidget(empty_state_label)

    proxy = PBSSidebarFilterProxy(tree_view)
    tree_view.setModel(proxy)

    return PBSSidebarPanel(
        sidebar=sidebar,
        filter_input=filter_input,
        tree_view=tree_view,
        empty_state_label=empty_state_label,
        proxy=proxy,
    )
