"""Qt-tabelmodel voor LCC-jaardetail (slice 28)."""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_desktop import messages
from rcm_desktop.adapter.lcc_planning_service import LCCYearDetailView
from rcm_desktop.formatting import format_eur, format_int

PASSIVE_COLUMN = 6


class LCCYearDetailTableModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._view: LCCYearDetailView | None = None
        self._show_passive_column = False
        self._headers = (
            messages.WORKSPACE_LCC_DETAIL_HEADER_PM,
            messages.WORKSPACE_LCC_DETAIL_HEADER_TYPE,
            messages.WORKSPACE_LCC_DETAIL_HEADER_FM,
            messages.WORKSPACE_LCC_DETAIL_HEADER_EXECUTIONS,
            messages.WORKSPACE_LCC_DETAIL_HEADER_COST,
            messages.WORKSPACE_LCC_DETAIL_HEADER_DOWNTIME,
            messages.WORKSPACE_LCC_DETAIL_HEADER_PASSIVE,
        )

    def set_view(
        self,
        view: LCCYearDetailView | None,
        *,
        passive_column: bool = False,
    ) -> None:
        self.beginResetModel()
        self._view = view
        self._show_passive_column = bool(passive_column)
        self.endResetModel()

    def detail_view(self) -> LCCYearDetailView | None:
        return self._view

    def pm_id_at(self, row: int) -> str | None:
        if self._view is None or row < 0 or row >= len(self._view.rows):
            return None
        return self._view.rows[row].pm_id

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        if self._view is None:
            return 0
        return len(self._view.rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return len(self._headers) if self._show_passive_column else len(self._headers) - 1

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.DisplayRole,
    ):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        if 0 <= section < self.columnCount():
            return self._headers[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: N802
        if not index.isValid() or self._view is None:
            return None
        row = index.row()
        col = index.column()
        if row < 0 or row >= len(self._view.rows):
            return None
        detail_row = self._view.rows[row]
        if role == Qt.DisplayRole:
            if col == 0:
                return detail_row.pm_label
            if col == 1:
                return detail_row.taak_type
            if col == 2:
                return detail_row.fm_display
            if col == 3:
                return format_int(detail_row.executions)
            if col == 4:
                return format_eur(detail_row.pm_cost_eur)
            if col == 5:
                return format_eur(detail_row.planned_downtime_hr)
            if col == PASSIVE_COLUMN and self._show_passive_column:
                return "✓" if detail_row.is_passive else ""
        if role == Qt.CheckStateRole and col == PASSIVE_COLUMN and self._show_passive_column:
            return Qt.CheckState.Checked if detail_row.is_passive else Qt.CheckState.Unchecked
        return None

    def flags(self, index: QModelIndex):  # noqa: N802
        base = super().flags(index)
        if (
            index.isValid()
            and self._show_passive_column
            and index.column() == PASSIVE_COLUMN
        ):
            return base | Qt.ItemIsUserCheckable
        return base
