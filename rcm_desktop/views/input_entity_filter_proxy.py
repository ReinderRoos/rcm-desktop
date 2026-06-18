"""Generieke Input-filter-proxy: PBS-scope ∧ globale zoekbalk (slice 87)."""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel

from rcm_desktop.adapter.view_core_facade import RCMProject

from rcm_desktop.adapter.entity_table_model import EntityTableModel
from rcm_desktop.adapter.input_scope_policy import row_in_scope


class InputEntityFilterProxy(QSortFilterProxyModel):
    def __init__(self, view_id: str, parent=None) -> None:
        super().__init__(parent)
        self._view_id = view_id
        self._scope_id: str | None = None
        self._project: RCMProject | None = None
        self._search = ""

    def set_scope(self, scope_id: str | None, project: RCMProject | None) -> None:
        self._scope_id = scope_id
        self._project = project
        self._refresh_filter()

    def set_search_text(self, text: str) -> None:
        self._search = (text or "").strip().lower()
        self._refresh_filter()

    def _refresh_filter(self) -> None:
        self.beginFilterChange()
        self.endFilterChange()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        src = self.sourceModel()
        if not isinstance(src, EntityTableModel):
            return True
        row_v = src.row_view_at(source_row)
        project = self._project
        if project is not None:
            if not row_in_scope(self._view_id, row_v.values, project, self._scope_id):
                return False
        if self._search:
            hay = src.search_haystack_at(source_row)
            if self._search not in hay:
                return False
        return True
