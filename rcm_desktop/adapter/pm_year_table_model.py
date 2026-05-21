"""Qt-tabelmodel voor PM-jaar-rijen (slice 23, issue 05).

Toont drie kolommen — kalenderjaar, waarde, cumulatief — waarbij de waarde-
en cumulatief-kolomheaders en hun formattering afhangen van de active
PM-submodus (`kosten` → EUR; `aantal_uitvoeringen` → integer count).
"""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_desktop import messages
from rcm_desktop.adapter.pm_chart_service import PMYearRow
from rcm_desktop.adapter.pm_chart_service import (
    PM_SUBMODE_AANTAL_UITVOERINGEN,
    PM_SUBMODE_KOSTEN,
)
from rcm_desktop.formatting import format_eur, format_int

RAW_ROLE = Qt.UserRole + 1


def _headers(submode: str) -> tuple[str, str, str]:
    if submode == PM_SUBMODE_AANTAL_UITVOERINGEN:
        return (
            messages.WORKSPACE_PM_TABLE_HEADER_KALENDERJAAR,
            messages.WORKSPACE_PM_TABLE_HEADER_WAARDE_AANTAL,
            messages.WORKSPACE_PM_TABLE_HEADER_CUMULATIEF_AANTAL,
        )
    return (
        messages.WORKSPACE_PM_TABLE_HEADER_KALENDERJAAR,
        messages.WORKSPACE_PM_TABLE_HEADER_WAARDE_KOSTEN,
        messages.WORKSPACE_PM_TABLE_HEADER_CUMULATIEF_KOSTEN,
    )


def _format_value(value: float, submode: str) -> str:
    if submode == PM_SUBMODE_AANTAL_UITVOERINGEN:
        return format_int(int(round(value)))
    return format_eur(value)


class PMYearTableModel(QAbstractTableModel):
    def __init__(
        self,
        rows: tuple[PMYearRow, ...] | list[PMYearRow],
        *,
        submode: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._rows: tuple[PMYearRow, ...] = tuple(
            sorted(rows, key=lambda r: r.calendar_year)
        )
        self._submode = submode
        self._headers = _headers(submode)

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
            and 0 <= section < len(self._headers)
        ):
            return self._headers[section]
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
                return row.value
            if column == 2:
                return row.cumulative
            return None
        if role != Qt.DisplayRole:
            return None
        if column == 0:
            return str(row.calendar_year)
        if column == 1:
            return _format_value(row.value, self._submode)
        if column == 2:
            return _format_value(row.cumulative, self._submode)
        return None
