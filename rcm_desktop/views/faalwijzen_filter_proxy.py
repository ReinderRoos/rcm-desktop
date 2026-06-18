"""Proxy-model voor faalwijzen-grid filters en zoek."""

from __future__ import annotations

from PySide6.QtCore import QSortFilterProxyModel, QModelIndex

from rcm_desktop.adapter.faalwijzen_table_model import FaalwijzenTableModel


class FaalwijzenFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._failure_type: str | None = None
        self._nmf_only: bool | None = None
        self._search = ""

    def set_failure_type_filter(self, value: str | None) -> None:
        self._failure_type = value
        self._refresh_filter()

    def set_nmf_filter(self, nmf_only: bool | None) -> None:
        self._nmf_only = nmf_only
        self._refresh_filter()

    def set_search_text(self, text: str) -> None:
        self._search = (text or "").strip().lower()
        self._refresh_filter()

    def _refresh_filter(self) -> None:
        # Qt marks invalidateFilter/invalidateRowsFilter as deprecated;
        # begin/endFilterChange is the supported replacement.
        self.beginFilterChange()
        self.endFilterChange()

    def source_table_model(self) -> FaalwijzenTableModel | None:
        model = self.sourceModel()
        return model if isinstance(model, FaalwijzenTableModel) else None

    def visible_fm_ids(self) -> list[str]:
        out: list[str] = []
        src = self.source_table_model()
        if src is None:
            return out
        for row in range(self.rowCount()):
            src_row = self.mapToSource(self.index(row, 0)).row()
            out.append(src.fm_id_at(src_row))
        return out

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        src = self.source_table_model()
        if src is None:
            return True
        row_v = src._row_at(source_row)
        values = row_v.values
        if self._failure_type is not None and values.get("failure_type") != self._failure_type:
            return False
        if self._nmf_only is True and values.get("is_evident", True):
            return False
        if self._nmf_only is False and not values.get("is_evident", True):
            return False
        if self._search:
            hay = f"{row_v.row_key} {values.get('faalwijze_omschrijving', '')}".lower()
            if self._search not in hay:
                return False
        return True
