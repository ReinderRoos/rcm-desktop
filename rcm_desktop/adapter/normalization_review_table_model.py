"""Qt-tabelmodel voor uniformeren review (slice 95 issue 10)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_desktop import messages
from rcm_desktop.adapter.normalization_review_presentation_service import (
    NormalizationReviewPresentation,
    NormalizationReviewRow,
)

_APPROVED_ROLE = Qt.ItemDataRole.UserRole + 1


class NormalizationReviewTableModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: tuple[NormalizationReviewRow, ...] = ()
        self._approved: set[int] = set()

    def set_presentation(self, presentation: NormalizationReviewPresentation | None) -> None:
        self.beginResetModel()
        self._rows = () if presentation is None else presentation.items
        self._approved = set()
        self.endResetModel()

    def row_at(self, row_index: int) -> NormalizationReviewRow | None:
        if row_index < 0 or row_index >= len(self._rows):
            return None
        return self._rows[row_index]

    def approved_indices(self) -> frozenset[int]:
        return frozenset(self._approved)

    def set_approved(self, index: int, approved: bool) -> None:
        if index < 0 or index >= len(self._rows):
            return
        if approved:
            self._approved.add(index)
        else:
            self._approved.discard(index)
        model_index = self.index(index, 0)
        self.dataChanged.emit(model_index, model_index, [Qt.CheckStateRole])

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent is not None and parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent is not None and parent.isValid():
            return 0
        return len(messages.NORMALIZATION_REVIEW_TABLE_HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # noqa: N802
        if orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return super().headerData(section, orientation, role)
        headers = messages.NORMALIZATION_REVIEW_TABLE_HEADERS
        if section < 0 or section >= len(headers):
            return None
        return headers[section]

    def flags(self, index: QModelIndex):  # noqa: N802
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        base = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == 0:
            return base | Qt.ItemFlag.ItemIsUserCheckable
        return base

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: N802
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        col = index.column()
        if role == Qt.CheckStateRole and col == 0:
            return Qt.CheckState.Checked if row.index in self._approved else Qt.CheckState.Unchecked
        if role != Qt.DisplayRole:
            return None
        if col == 0:
            return ""
        if col == 1:
            return row.fm_id_a or "—"
        if col == 2:
            return row.fm_id_b or "—"
        if col == 3:
            return row.field
        if col == 4:
            return row.source_label
        if col == 5:
            return str(row.proposed_value)
        return None

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole):  # noqa: N802
        if not index.isValid() or index.column() != 0 or role != Qt.CheckStateRole:
            return False
        row = self._rows[index.row()]
        approved = value == Qt.CheckState.Checked
        self.set_approved(row.index, approved)
        return True
