from __future__ import annotations

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt

from rcm_core.models import RCMProject
from rcm_desktop import messages
from rcm_desktop.adapter.rcm_navigation_tree_builder import (
    RcmNavigationNode,
    scope_pbs_id_for_node,
)
class RcmNavigationTreeModel(QAbstractItemModel):
    """Sidebar-boom PBS → functie → faalwijze; totalen tonen `—` vóór run."""

    _COLUMN_FIELDS = (
        "node_id",
        "label",
        "placeholder_failures",
        "placeholder_downtime",
        "placeholder_unavail",
        "placeholder_cost",
    )
    _HEADERS = (
        messages.PBS_RESULTS_HEADER_PBS_ID,
        messages.PBS_RESULTS_HEADER_BOUWDEEL,
        messages.PBS_RESULTS_HEADER_FAALMOMENTEN_TOTAL,
        messages.PBS_RESULTS_HEADER_DOWNTIME_TOTAL_HR,
        messages.PBS_RESULTS_HEADER_UNAVAILABILITY_TOTAL,
        messages.PBS_RESULTS_HEADER_COST_TOTAL_EUR,
    )
    EMPTY_PLACEHOLDER = "—"

    def __init__(
        self,
        roots: tuple[RcmNavigationNode, ...],
        project: RCMProject,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._roots = roots
        self._project = project
        self._parent_of: dict[RcmNavigationNode, RcmNavigationNode | None] = {}
        for root in roots:
            self._register_parent(root, None)

    def scope_pbs_id_for_index(self, index: QModelIndex) -> str | None:
        if not index.isValid():
            return None
        node = index.internalPointer()
        if not isinstance(node, RcmNavigationNode):
            return None
        return scope_pbs_id_for_node(node, self._project)

    def _register_parent(
        self, node: RcmNavigationNode, par: RcmNavigationNode | None
    ) -> None:
        self._parent_of[node] = par
        for child in node.children:
            self._register_parent(child, node)

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        if parent is None or not parent.isValid():
            return len(self._roots)
        node = parent.internalPointer()
        assert isinstance(node, RcmNavigationNode)
        return len(node.children)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        return len(self._COLUMN_FIELDS)

    def index(self, row: int, column: int, parent: QModelIndex | None = None) -> QModelIndex:
        if parent is None:
            parent = QModelIndex()
        if column < 0 or column >= len(self._COLUMN_FIELDS):
            return QModelIndex()
        if row < 0:
            return QModelIndex()
        if not parent.isValid():
            if row >= len(self._roots):
                return QModelIndex()
            return self.createIndex(row, column, self._roots[row])
        pnode = parent.internalPointer()
        assert isinstance(pnode, RcmNavigationNode)
        if row >= len(pnode.children):
            return QModelIndex()
        return self.createIndex(row, column, pnode.children[row])

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        child = index.internalPointer()
        assert isinstance(child, RcmNavigationNode)
        par = self._parent_of.get(child)
        if par is None:
            return QModelIndex()
        gp = self._parent_of[par]
        siblings = list(self._roots if gp is None else gp.children)
        row = siblings.index(par)
        return self.createIndex(row, 0, par)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and 0 <= section < len(
            self._HEADERS
        ):
            return self._HEADERS[section]
        return super().headerData(section, orientation, role)

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        node = index.internalPointer()
        assert isinstance(node, RcmNavigationNode)
        if role != Qt.DisplayRole:
            return None
        column_name = self._COLUMN_FIELDS[index.column()]
        if column_name == "node_id":
            return node.node_id
        if column_name == "label":
            return node.label
        return self.EMPTY_PLACEHOLDER
