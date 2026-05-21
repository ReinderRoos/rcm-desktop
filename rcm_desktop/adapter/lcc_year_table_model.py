"""Qt-tabelmodel voor LCC-jaarbuckets (slice 23, fase C — issue 03).

Toont vier kolommen — kalenderjaar, correctief EUR, preventief EUR, totaal EUR —
voor een tuple `LCCYearBucket`. Rijen worden oplopend op kalenderjaar gesorteerd
zodat de tabel altijd dezelfde volgorde heeft als de gestapelde staafgrafiek.
"""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_desktop import messages
from rcm_desktop.adapter.lcc_chart_service import LCCYearBucket
from rcm_desktop.formatting import format_eur

RAW_ROLE = Qt.UserRole + 1

_HEADERS = (
    messages.WORKSPACE_LCC_TABLE_HEADER_KALENDERJAAR,
    messages.WORKSPACE_LCC_TABLE_HEADER_CORRECTIEF,
    messages.WORKSPACE_LCC_TABLE_HEADER_PREVENTIEF,
    messages.WORKSPACE_LCC_TABLE_HEADER_TOTAAL,
)


class LCCYearTableModel(QAbstractTableModel):
    def __init__(
        self,
        buckets: tuple[LCCYearBucket, ...] | list[LCCYearBucket],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._buckets: tuple[LCCYearBucket, ...] = tuple(
            sorted(buckets, key=lambda b: b.calendar_year)
        )

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return len(self._buckets)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return 4

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
        bucket = self._buckets[index.row()]
        column = index.column()
        total_eur = bucket.correctief_eur + bucket.preventief_eur
        if role == RAW_ROLE:
            if column == 0:
                return bucket.calendar_year
            if column == 1:
                return bucket.correctief_eur
            if column == 2:
                return bucket.preventief_eur
            if column == 3:
                return total_eur
            return None
        if role != Qt.DisplayRole:
            return None
        if column == 0:
            return str(bucket.calendar_year)
        if column == 1:
            return format_eur(bucket.correctief_eur)
        if column == 2:
            return format_eur(bucket.preventief_eur)
        if column == 3:
            return format_eur(total_eur)
        return None
