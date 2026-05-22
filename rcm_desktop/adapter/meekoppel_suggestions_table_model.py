"""Tabelmodel meekoppelkansen (slice 39)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_desktop import messages
from rcm_desktop.adapter.meekoppelkansen_discovery_service import MeekoppelSuggestion

_HEADERS = (
    messages.WORKSPACE_MEEKOPPEL_HEADER_ELEMENT,
    messages.WORKSPACE_MEEKOPPEL_HEADER_PM_A,
    messages.WORKSPACE_MEEKOPPEL_HEADER_PM_B,
    messages.WORKSPACE_MEEKOPPEL_HEADER_JAAR_A,
    messages.WORKSPACE_MEEKOPPEL_HEADER_JAAR_B,
    messages.WORKSPACE_MEEKOPPEL_HEADER_DELTA,
    messages.WORKSPACE_MEEKOPPEL_HEADER_REDEN,
)


class MeekoppelSuggestionsTableModel(QAbstractTableModel):
    def __init__(
        self,
        rows: tuple[MeekoppelSuggestion, ...] = (),
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._rows = rows

    def set_rows(self, rows: tuple[MeekoppelSuggestion, ...]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def row_at(self, row: int) -> MeekoppelSuggestion | None:
        if row < 0 or row >= len(self._rows):
            return None
        return self._rows[row]

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return len(_HEADERS)

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ):
        if (
            role == Qt.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and 0 <= section < len(_HEADERS)
        ):
            return _HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: N802
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        r = self._rows[index.row()]
        col = index.column()
        if col == 0:
            return r.element_naam
        if col == 1:
            return r.pm_a
        if col == 2:
            return r.pm_b
        if col == 3:
            return str(r.jaar_a)
        if col == 4:
            return str(r.jaar_b)
        if col == 5:
            return str(r.jaar_delta)
        if col == 6:
            return r.reden
        return None
