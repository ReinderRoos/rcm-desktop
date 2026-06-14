from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_desktop import messages
from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow
from rcm_desktop.formatting import format_eur, format_float, format_int


class FMMCResultsTableModel(QAbstractTableModel):
    _COLUMNS = (
        "fm_id",
        "bouwdeel_naam",
        "faalwijze_omschrijving",
        "is_nmf",
        "rf",
        "failures_p50",
        "downtime_p50",
        "cost_p50",
    )
    _HEADERS = (
        messages.FM_RESULTS_HEADER_FM_ID,
        messages.FM_RESULTS_HEADER_BOUWDEEL_NAAM,
        messages.FM_RESULTS_HEADER_FAALWIJZE,
        messages.FM_RESULTS_HEADER_NMF,
        messages.FM_RESULTS_HEADER_RF,
        messages.FM_MC_RESULTS_HEADER_FAALMOMENTEN,
        messages.FM_MC_RESULTS_HEADER_DOWNTIME_HR,
        messages.FM_MC_RESULTS_HEADER_TOTAL_COST_EUR,
    )

    def __init__(self, rows: list[FMMCResultRow], parent=None) -> None:
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
        if role == Qt.ToolTipRole and orientation == Qt.Horizontal and section in (5, 6, 7):
            return messages.SIMULATION_MC_FM_MODE_BADGE
        return super().headerData(section, orientation, role)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        column_name = self._COLUMNS[index.column()]
        if role == Qt.UserRole + 1:
            if column_name == "failures_p50":
                return row.failures_band.p50
            if column_name == "downtime_p50":
                return row.downtime_band.p50
            if column_name == "cost_p50":
                return row.cost_band.p50
            return getattr(row, column_name.replace("_p50", ""), getattr(row, column_name, ""))
        if role == Qt.ToolTipRole:
            if column_name == "failures_p50":
                band = row.failures_band
            elif column_name == "downtime_p50":
                band = row.downtime_band
            elif column_name == "cost_p50":
                band = row.cost_band
            else:
                return None
            return messages.FM_MC_RESULTS_BAND_TOOLTIP.format(
                p10=format_float(band.p10),
                p90=format_float(band.p90),
            )
        if role != Qt.DisplayRole:
            return None
        if column_name == "is_nmf":
            return messages.FM_RESULTS_NMF_YES if row.is_nmf else ""
        if column_name == "rf":
            return "" if row.rf == 0.0 else format_float(row.rf)
        if column_name == "failures_p50":
            return format_int(int(round(row.failures_band.p50)))
        if column_name == "downtime_p50":
            return format_float(row.downtime_band.p50)
        if column_name == "cost_p50":
            return format_eur(row.cost_band.p50)
        return str(getattr(row, column_name))
