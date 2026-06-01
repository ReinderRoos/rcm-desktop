"""Tabelmodel meekoppelkansen per PBS-locatie (slice 40/41, UX v2)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_desktop.adapter.meekoppel_panel_service import MeekoppelPanelColumn, MeekoppelPanelRow


class MeekoppelSuggestionsTableModel(QAbstractTableModel):
    def __init__(
        self,
        rows: tuple[MeekoppelPanelRow, ...] = (),
        columns: tuple[MeekoppelPanelColumn, ...] = (),
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._rows = rows
        self._headers = tuple(c.header for c in columns)

    def set_panel_rows(
        self,
        rows: tuple[MeekoppelPanelRow, ...],
        *,
        columns: tuple[MeekoppelPanelColumn, ...],
    ) -> None:
        self.beginResetModel()
        self._rows = rows
        self._headers = tuple(c.header for c in columns)
        self.endResetModel()

    def row_at(self, row: int) -> MeekoppelPanelRow | None:
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
        return len(self._headers)

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ):
        if (
            role == Qt.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and 0 <= section < len(self._headers)
        ):
            return self._headers[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: N802
        if not index.isValid():
            return None
        r = self._rows[index.row()]
        col = index.column()
        if role == Qt.ToolTipRole and col == 0:
            return r.path_tooltip
        if role != Qt.DisplayRole:
            return None
        if col == 0:
            return r.path_label
        if col == 1:
            return r.rev_count_text
        if col == 2:
            return r.due_range_text
        if col == 3:
            return r.span_text
        return None
