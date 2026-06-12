from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt

from rcm_desktop import messages
from rcm_desktop.adapter.result_view_service import FMResultRow
from rcm_desktop.formatting import format_eur, format_float, format_int

RAW_ROLE = Qt.UserRole + 1

_NUMERIC_SORT_COLS = frozenset({4, 5, 6, 7})


class FMResultsSortProxy(QSortFilterProxyModel):
    """Sort proxy: numerieke kolommen via RAW float, tekst via case-insensitive string."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSortRole(RAW_ROLE)
        self.setDynamicSortFilter(True)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:  # noqa: N802
        col = left.column()
        src = self.sourceModel()
        if src is None:
            return False
        # Qt passes source-model indices to lessThan (not proxy indices).
        lv = src.data(left, RAW_ROLE)
        rv = src.data(right, RAW_ROLE)
        if col in _NUMERIC_SORT_COLS:
            try:
                return float(lv) < float(rv)
            except (TypeError, ValueError):
                return False
        return str(lv).casefold() < str(rv).casefold()


class FMResultsTableModel(QAbstractTableModel):
    _COLUMNS = (
        "fm_id",
        "bouwdeel_naam",
        "faalwijze_omschrijving",
        "is_nmf",
        "rf",
        "expected_failures",
        "expected_total_downtime_hr",
        "total_cost_eur",
        "pbs_id",
    )
    _HEADERS = (
        messages.FM_RESULTS_HEADER_FM_ID,
        messages.FM_RESULTS_HEADER_BOUWDEEL_NAAM,
        messages.FM_RESULTS_HEADER_FAALWIJZE,
        messages.FM_RESULTS_HEADER_NMF,
        messages.FM_RESULTS_HEADER_RF,
        messages.FM_RESULTS_HEADER_FAALMOMENTEN,
        messages.FM_RESULTS_HEADER_DOWNTIME_HR,
        messages.FM_RESULTS_HEADER_TOTAL_COST_EUR,
        messages.FM_RESULTS_HEADER_PBS_ID,
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
        if column_name == "is_nmf":
            return messages.FM_RESULTS_NMF_YES if value else ""
        if column_name == "rf":
            return "" if value == 0.0 and not row.rf_tooltip_entries else format_float(value)
        if column_name == "expected_failures":
            return format_int(int(round(value)))
        if column_name == "expected_total_downtime_hr":
            return format_float(value)
        if column_name == "total_cost_eur":
            return format_eur(value)
        return str(value)
