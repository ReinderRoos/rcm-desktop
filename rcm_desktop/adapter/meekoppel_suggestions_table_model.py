"""Tabelmodel meekoppelkansen per PBS-locatie (slice 40, UX v2)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from rcm_core.models import RCMProject

from rcm_desktop import messages
from rcm_desktop.adapter.meekoppel_display_service import location_group_tooltip
from rcm_desktop.adapter.meekoppelkansen_discovery_service import MeekoppelLocationGroup

_HEADERS = (
    messages.WORKSPACE_MEEKOPPEL_HEADER_PATH,
    messages.WORKSPACE_MEEKOPPEL_HEADER_REV_COUNT,
    messages.WORKSPACE_MEEKOPPEL_HEADER_DUE_RANGE,
    messages.WORKSPACE_MEEKOPPEL_HEADER_SPAN,
)


class MeekoppelSuggestionsTableModel(QAbstractTableModel):
    def __init__(
        self,
        rows: tuple[MeekoppelLocationGroup, ...] = (),
        project: RCMProject | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._rows = rows
        self._project = project

    def set_rows(
        self,
        rows: tuple[MeekoppelLocationGroup, ...],
        *,
        project: RCMProject | None = None,
    ) -> None:
        self.beginResetModel()
        self._rows = rows
        if project is not None:
            self._project = project
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
        if not index.isValid():
            return None
        r = self._rows[index.row()]
        col = index.column()
        if role == Qt.ToolTipRole and col == 0 and self._project is not None:
            return location_group_tooltip(self._project, r)
        if role != Qt.DisplayRole:
            return None
        if col == 0:
            return r.path_label
        if col == 1:
            return str(r.rev_count)
        if col == 2:
            return r.due_range_label()
        if col == 3:
            return str(r.span_jaar)
        return None
