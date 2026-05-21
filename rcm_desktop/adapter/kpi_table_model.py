"""Qt-tabelmodel voor de gedeelde KPI-tabel.

Kolommen: 0 = label (`KPI`), 1 = "Huidige analyse".
"""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_desktop.adapter.kpi_table_service import KPITable

RAW_ROLE = Qt.UserRole + 1


class KPITableModel(QAbstractTableModel):
    def __init__(self, table: KPITable, parent=None) -> None:
        super().__init__(parent)
        self._table = table

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return len(self._table.rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return 1 + len(self._table.scenario_keys)

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ):
        if orientation != Qt.Horizontal:
            return super().headerData(section, orientation, role)
        if role == Qt.DisplayRole:
            if section == 0:
                return "KPI"
            idx = section - 1
            if idx < 0 or idx >= len(self._table.scenario_labels):
                return None
            return self._table.scenario_labels[idx]
        return super().headerData(section, orientation, role)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._table.rows[index.row()]
        column = index.column()
        if role == RAW_ROLE:
            if column == 0:
                return row.key
            cell_idx = column - 1
            if cell_idx < 0 or cell_idx >= len(row.cells):
                return None
            return row.cells[cell_idx].raw
        if role != Qt.DisplayRole:
            return None
        if column == 0:
            return row.label
        cell_idx = column - 1
        if cell_idx < 0 or cell_idx >= len(row.cells):
            return None
        return row.cells[cell_idx].display
