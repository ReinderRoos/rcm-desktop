"""Qt-tabelmodel voor vergelijkingswerkruimte FM-lijst (slice 95 issue 07, slice 96)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from rcm_desktop import messages
from rcm_desktop.adapter.compare_workspace_presentation_service import CompareWorkspaceRow
from rcm_desktop.adapter.scenario_compare_chrome import scenario_color_hex
from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A, COMPARE_SLOT_B

ROW_ROLE = Qt.UserRole + 1
BADGE_ROLE = Qt.UserRole + 2
HIGHLIGHT_ROLE = Qt.UserRole + 3
SIDE_A_COLOR_ROLE = Qt.UserRole + 4
SIDE_B_COLOR_ROLE = Qt.UserRole + 5

_HEADERS = (
    messages.COMPARE_MODELS_TABLE_HEADER_STATUS,
    messages.COMPARE_MODELS_TABLE_HEADER_MATCH,
    messages.COMPARE_MODELS_TABLE_HEADER_FM_A,
    messages.COMPARE_MODELS_TABLE_HEADER_FM_B,
    messages.COMPARE_MODELS_TABLE_HEADER_CLASS,
    messages.COMPARE_MODELS_TABLE_HEADER_FIELD_DIFFS,
    messages.COMPARE_MODELS_TABLE_HEADER_RESULT_DIFFS,
)


class CompareWorkspaceTableModel(QAbstractTableModel):
    def __init__(
        self,
        rows: tuple[CompareWorkspaceRow, ...] = (),
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._rows = rows

    def set_rows(self, rows: tuple[CompareWorkspaceRow, ...]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def row_at(self, row: int) -> CompareWorkspaceRow | None:
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
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.DisplayRole,
    ):
        if orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return super().headerData(section, orientation, role)
        if section < 0 or section >= len(_HEADERS):
            return None
        return _HEADERS[section]

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        column = index.column()
        if role == ROW_ROLE:
            return row
        if role == BADGE_ROLE:
            return row.match_badge
        if role == SIDE_A_COLOR_ROLE:
            return QColor(scenario_color_hex(COMPARE_SLOT_A))
        if role == SIDE_B_COLOR_ROLE:
            return QColor(scenario_color_hex(COMPARE_SLOT_B))
        if role == Qt.ForegroundRole:
            if column == 2:
                return QColor(scenario_color_hex(COMPARE_SLOT_A))
            if column == 3:
                return QColor(scenario_color_hex(COMPARE_SLOT_B))
        if role != Qt.DisplayRole:
            return None
        if column == 0:
            return row.status_label
        if column == 1:
            return row.match_badge
        if column == 2:
            return row.fm_id_a or "—"
        if column == 3:
            return row.fm_id_b or "—"
        if column == 4:
            return row.difference_class
        if column == 5:
            return str(row.field_diff_count)
        if column == 6:
            return str(row.result_diff_count)
        return None
