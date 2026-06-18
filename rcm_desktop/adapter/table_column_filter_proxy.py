"""Generieke kolomfilter-proxy (slice 81)."""

from __future__ import annotations

from PySide6.QtCore import QSortFilterProxyModel, Qt

from rcm_desktop.adapter.table_filter_parser import (
    BoolFilterPredicate,
    NumericFilterPredicate,
    TextFilterPredicate,
    parse_bool_filter,
    parse_numeric_filter,
    parse_text_filter,
    row_matches_column_filters,
)


class TableColumnFilterProxy(QSortFilterProxyModel):
    """Filter-proxy zonder domeinkennis; kolomtypen komen via configuratie."""

    def __init__(
        self,
        *,
        text_columns: frozenset[int],
        bool_columns: frozenset[int] = frozenset(),
        numeric_columns: frozenset[int] = frozenset(),
        raw_role: int = Qt.UserRole + 1,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._text_columns = text_columns
        self._bool_columns = bool_columns
        self._numeric_columns = numeric_columns
        self._raw_role = raw_role
        self._text_filters: dict[int, str] = {}
        self._bool_filters: dict[int, bool | None] = {}
        self._numeric_filters: dict[int, str] = {}
        self._text_preds: dict[int, TextFilterPredicate] = {}
        self._bool_preds: dict[int, BoolFilterPredicate] = {}
        self._numeric_preds: dict[int, NumericFilterPredicate] = {}
        self._invalid_numeric_columns: frozenset[int] = frozenset()

    def set_text_filter(self, column: int, raw: str) -> None:
        self._text_filters[column] = raw
        self._rebuild_predicates()
        self.invalidateFilter()

    def set_bool_filter(self, column: int, required: bool | None) -> None:
        self._bool_filters[column] = required
        self._rebuild_predicates()
        self.invalidateFilter()

    def set_numeric_filter(self, column: int, raw: str) -> None:
        self._numeric_filters[column] = raw
        self._rebuild_predicates()
        self.invalidateFilter()

    def clear_filters(self) -> None:
        self._text_filters.clear()
        self._bool_filters.clear()
        self._numeric_filters.clear()
        self._rebuild_predicates()
        self.invalidateFilter()

    def text_filters(self) -> dict[int, str]:
        return dict(self._text_filters)

    def bool_filters(self) -> dict[int, bool | None]:
        return dict(self._bool_filters)

    def numeric_filters(self) -> dict[int, str]:
        return dict(self._numeric_filters)

    def invalid_numeric_columns(self) -> frozenset[int]:
        return self._invalid_numeric_columns

    def _rebuild_predicates(self) -> None:
        self._text_preds = {
            col: parse_text_filter(raw)
            for col, raw in self._text_filters.items()
            if col in self._text_columns and raw.strip()
        }
        self._bool_preds = {
            col: parse_bool_filter(required)
            for col, required in self._bool_filters.items()
            if col in self._bool_columns and required is not None
        }
        numeric_preds: dict[int, NumericFilterPredicate] = {}
        invalid: set[int] = set()
        for col, raw in self._numeric_filters.items():
            if col in self._numeric_columns and raw.strip():
                parsed = parse_numeric_filter(raw)
                numeric_preds[col] = parsed.predicate
                if parsed.invalid:
                    invalid.add(col)
        self._numeric_preds = numeric_preds
        self._invalid_numeric_columns = frozenset(invalid)

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:  # noqa: N802
        src = self.sourceModel()
        if src is None:
            return True
        if not self._text_preds and not self._bool_preds and not self._numeric_preds:
            return True

        needed_cols = set(self._text_preds) | set(self._bool_preds) | set(self._numeric_preds)
        raw_by_col: dict[int, object] = {}
        for col in needed_cols:
            idx = src.index(source_row, col, source_parent)
            raw_by_col[col] = src.data(idx, self._raw_role)

        return row_matches_column_filters(
            raw_by_col,
            text=self._text_preds,
            bool_=self._bool_preds,
            numeric=self._numeric_preds,
        )
