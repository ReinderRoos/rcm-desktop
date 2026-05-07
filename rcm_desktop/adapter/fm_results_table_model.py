from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_desktop import messages
from rcm_desktop.adapter.result_view_service import FMResultRow
from rcm_desktop.formatting import format_eur, format_float, format_int

RAW_ROLE = Qt.UserRole + 1


class FMResultsTableModel(QAbstractTableModel):
    _COLUMNS = (
        "fm_id",
        "faalwijze_omschrijving",
        "pbs_id",
        "bouwdeel_naam",
        "expected_failures",
        "expected_total_downtime_hr",
        "total_cost_eur",
    )
    _HEADERS = (
        messages.FM_RESULTS_HEADER_FM_ID,
        messages.FM_RESULTS_HEADER_FAALWIJZE,
        messages.FM_RESULTS_HEADER_PBS_ID,
        messages.FM_RESULTS_HEADER_BOUWDEEL_NAAM,
        messages.FM_RESULTS_HEADER_FAALMOMENTEN,
        messages.FM_RESULTS_HEADER_DOWNTIME_HR,
        messages.FM_RESULTS_HEADER_TOTAL_COST_EUR,
    )

    def __init__(self, rows: list[FMResultRow], parent=None) -> None:
        super().__init__(parent)
        self._rows = list(rows)

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        if parent and parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        if parent and parent.isValid():
            return 0
        return len(self._COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and 0 <= section < len(self._HEADERS):
            return self._HEADERS[section]
        return super().headerData(section, orientation, role)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        column_name = self._COLUMNS[index.column()]
        value = getattr(row, column_name)
        if role == RAW_ROLE:
            return value
        if role != Qt.DisplayRole:
            return None
        if column_name == "expected_failures":
            return format_int(int(round(value)))
        if column_name == "expected_total_downtime_hr":
            return format_float(value)
        if column_name == "total_cost_eur":
            return format_eur(value)
        return str(value)
