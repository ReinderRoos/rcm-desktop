from __future__ import annotations

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt

from rcm_desktop import messages
from rcm_desktop.adapter.result_view_service import PBSTreeNode
from rcm_desktop.formatting import format_eur, format_float, format_int


class PBSResultsTreeModel(QAbstractItemModel):
    """Read-only boom op `PBSTreeNode`-roots (aggregaat-totalen uit `PBSResultRow`)."""

    _COLUMN_FIELDS = (
        "pbs_id",
        "bouwdeel_naam",
        "expected_failures_total",
        "total_downtime_hr_total",
        "unavailability_pct_total",
        "total_cost_eur_total",
    )
    _HEADERS = (
        messages.PBS_RESULTS_HEADER_PBS_ID,
        messages.PBS_RESULTS_HEADER_BOUWDEEL,
        messages.PBS_RESULTS_HEADER_FAALMOMENTEN_TOTAL,
        messages.PBS_RESULTS_HEADER_DOWNTIME_TOTAL_HR,
        messages.PBS_RESULTS_HEADER_UNAVAILABILITY_TOTAL,
        messages.PBS_RESULTS_HEADER_COST_TOTAL_EUR,
    )

    _NUMERIC_FIELDS = frozenset({
        "expected_failures_total",
        "total_downtime_hr_total",
        "unavailability_pct_total",
        "total_cost_eur_total",
    })
    EMPTY_PLACEHOLDER = "—"

    def __init__(
        self,
        roots: tuple[PBSTreeNode, ...],
        parent=None,
        *,
        show_totals: bool = True,
    ) -> None:
        super().__init__(parent)
        self._roots = roots
        self._show_totals = show_totals
        self._parent_of: dict[PBSTreeNode, PBSTreeNode | None] = {}
        for root in roots:
            self._register_parent(root, None)

    def pbs_id_for_index(self, index: QModelIndex) -> str | None:
        if not index.isValid():
            return None
        node = index.internalPointer()
        if not isinstance(node, PBSTreeNode):
            return None
        return node.pbs_id

    def _register_parent(self, node: PBSTreeNode, par: PBSTreeNode | None) -> None:
        self._parent_of[node] = par
        for child in node.children:
            self._register_parent(child, node)

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        if parent is None or not parent.isValid():
            return len(self._roots)
        node = parent.internalPointer()
        assert isinstance(node, PBSTreeNode)
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
        assert isinstance(pnode, PBSTreeNode)
        if row >= len(pnode.children):
            return QModelIndex()
        return self.createIndex(row, column, pnode.children[row])

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        child = index.internalPointer()
        assert isinstance(child, PBSTreeNode)
        par = self._parent_of.get(child)
        if par is None:
            return QModelIndex()
        gp = self._parent_of[par]
        siblings = list(self._roots if gp is None else gp.children)
        row = siblings.index(par)
        return self.createIndex(row, 0, par)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and 0 <= section < len(self._HEADERS):
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
        assert isinstance(node, PBSTreeNode)
        row = node.row
        column_name = self._COLUMN_FIELDS[index.column()]
        value = getattr(row, column_name)
        if role != Qt.DisplayRole:
            return None
        if column_name == "pbs_id":
            return str(value)
        if column_name == "bouwdeel_naam":
            return str(value)
        if not self._show_totals and column_name in self._NUMERIC_FIELDS:
            return self.EMPTY_PLACEHOLDER
        if column_name == "expected_failures_total":
            return format_int(int(round(value)))
        if column_name == "total_downtime_hr_total":
            return format_float(value)
        if column_name == "unavailability_pct_total":
            return f"{format_float(value)}%"
        if column_name == "total_cost_eur_total":
            return format_eur(value)
        return str(value)
