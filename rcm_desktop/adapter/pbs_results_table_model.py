from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_desktop import messages
from rcm_desktop.adapter.result_view_service import PBSResultRow
from rcm_desktop.formatting import format_eur, format_float, format_int

RAW_ROLE = Qt.UserRole + 1


class PBSResultsTableModel(QAbstractTableModel):
    _COLUMNS = (
        "pbs_id",
        "bouwdeel_naam",
        "level",
        "expected_failures_total",
        "total_downtime_hr_total",
        "unavailability_pct_total",
        "total_cost_eur_total",
    )
    _HEADERS = (
        messages.PBS_RESULTS_HEADER_PBS_ID,
        messages.PBS_RESULTS_HEADER_BOUWDEEL,
        messages.PBS_RESULTS_HEADER_LEVEL,
        messages.PBS_RESULTS_HEADER_FAALMOMENTEN_TOTAL,
        messages.PBS_RESULTS_HEADER_DOWNTIME_TOTAL_HR,
        messages.PBS_RESULTS_HEADER_UNAVAILABILITY_TOTAL,
        messages.PBS_RESULTS_HEADER_COST_TOTAL_EUR,
    )

    def __init__(self, rows: list[PBSResultRow], parent=None) -> None:
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
            if column_name == "bouwdeel_naam":
                return row.bouwdeel_naam
            return value
        if role != Qt.DisplayRole:
            return None
        if column_name == "bouwdeel_naam":
            return f"{'  ' * row.level}{row.bouwdeel_naam}"
        if column_name == "level":
            return format_int(row.level)
        if column_name == "expected_failures_total":
            return format_int(int(round(value)))
        if column_name == "total_downtime_hr_total":
            return format_float(value)
        if column_name == "unavailability_pct_total":
            return f"{format_float(value)}%"
        if column_name == "total_cost_eur_total":
            return format_eur(value)
        return str(value)
