"""Qt-tabelmodel voor niet-beschikbaarheid-jaar-rijen (slice 23, issue 04).

Toont drie kolommen — kalenderjaar, niet-beschikbaarheid %, downtime uren —
voor een tuple `UnavailabilityYearRow`. Rijen worden oplopend op kalenderjaar
gesorteerd zodat tabel en bijbehorende staafgrafiek consistent zijn.
"""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_desktop import messages
from rcm_desktop.adapter.unavailability_chart_service import UnavailabilityYearRow
from rcm_desktop.formatting import format_float

RAW_ROLE = Qt.UserRole + 1

_HEADERS = (
    messages.WORKSPACE_UNAVAILABILITY_TABLE_HEADER_KALENDERJAAR,
    messages.WORKSPACE_UNAVAILABILITY_TABLE_HEADER_PCT,
    messages.WORKSPACE_UNAVAILABILITY_TABLE_HEADER_DOWNTIME,
)


class UnavailabilityYearTableModel(QAbstractTableModel):
    def __init__(
        self,
        rows: tuple[UnavailabilityYearRow, ...] | list[UnavailabilityYearRow],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._rows: tuple[UnavailabilityYearRow, ...] = tuple(
            sorted(rows, key=lambda r: r.calendar_year)
        )

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return 3

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ):
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
        column = index.column()
        if role == RAW_ROLE:
            if column == 0:
                return row.calendar_year
            if column == 1:
                return row.unavailability_pct
            if column == 2:
                return row.downtime_hr
            return None
        if role != Qt.DisplayRole:
            return None
        if column == 0:
            return str(row.calendar_year)
        if column == 1:
            return f"{format_float(row.unavailability_pct, decimals=4)} %"
        if column == 2:
            return format_float(row.downtime_hr)
        return None
