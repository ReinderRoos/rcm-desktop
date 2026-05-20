"""Jaartabel voor FM-inspector (slice 34)."""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_desktop import messages
from rcm_desktop.adapter.fm_verification_service import FMVerificationYearRow
from rcm_desktop.formatting import format_eur, format_float

_HEADERS = (
    messages.WORKSPACE_FM_INSPECTOR_YEAR_HEADER_KALENDERJAAR,
    messages.WORKSPACE_FM_INSPECTOR_YEAR_HEADER_FAALMOMENTEN,
    messages.WORKSPACE_FM_INSPECTOR_YEAR_HEADER_COR_EUR,
    messages.WORKSPACE_FM_INSPECTOR_YEAR_HEADER_DOWNTIME,
    messages.WORKSPACE_FM_INSPECTOR_YEAR_HEADER_HIDDEN_NB,
)


class FMVerificationYearTableModel(QAbstractTableModel):
    def __init__(
        self,
        rows: tuple[FMVerificationYearRow, ...] | list[FMVerificationYearRow],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._rows = tuple(rows)

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        if parent and parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        if parent and parent.isValid():
            return 0
        return len(_HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if (
            role == Qt.DisplayRole
            and orientation == Qt.Horizontal
            and 0 <= section < len(_HEADERS)
        ):
            return _HEADERS[section]
        return super().headerData(section, orientation, role)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        col = index.column()
        if role != Qt.DisplayRole:
            return None
        if col == 0:
            return str(row.calendar_year)
        if col == 1:
            return format_float(row.faalmomenten)
        if col == 2:
            return format_eur(row.cor_eur)
        if col == 3:
            return format_float(row.cor_downtime_hr)
        if col == 4:
            return format_float(row.hidden_nb_hr)
        return None
