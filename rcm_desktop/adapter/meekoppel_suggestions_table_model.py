"""Tabelmodel meekoppelkansen per PBS-locatie (slice 40)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_desktop import messages
from rcm_desktop.adapter.meekoppelkansen_discovery_service import MeekoppelLocationGroup

_HEADERS = (
    messages.WORKSPACE_MEEKOPPEL_HEADER_PATH,
    messages.WORKSPACE_MEEKOPPEL_HEADER_PBS_ID,
    messages.WORKSPACE_MEEKOPPEL_HEADER_REV_COUNT,
    messages.WORKSPACE_MEEKOPPEL_HEADER_DUE_RANGE,
    messages.WORKSPACE_MEEKOPPEL_HEADER_SPAN,
)


class MeekoppelSuggestionsTableModel(QAbstractTableModel):
    def __init__(
        self,
        rows: tuple[MeekoppelLocationGroup, ...] = (),
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._rows = rows

    def set_rows(self, rows: tuple[MeekoppelLocationGroup, ...]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def row_at(self, row: int) -> MeekoppelLocationGroup | None:
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
            return r.path_label
        if col == 1:
            return r.pbs_id
        if col == 2:
            return str(r.rev_count)
        if col == 3:
            return r.due_range_label()
        if col == 4:
            return str(r.span_jaar)
        return None
