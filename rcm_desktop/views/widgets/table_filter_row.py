"""Generieke tabel-filterrij-widget (slice 81)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QHeaderView, QLineEdit, QWidget

from rcm_desktop import messages
from rcm_desktop.adapter.table_filter_parser import TableColumnFilterKind

_FILTER_INVALID_STYLE = "border: 1px solid #E65100;"


class TableFilterRowWidget(QWidget):
    """Per-kolom filtervelden; breedtes volgen de tabelheader."""

    filters_changed = Signal()

    def __init__(
        self,
        column_kinds: dict[int, TableColumnFilterKind],
        *,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._column_kinds = dict(column_kinds)
        self._cells: dict[int, QWidget] = {}
        self._text_edits: dict[int, QLineEdit] = {}
        self._bool_combos: dict[int, QComboBox] = {}
        self._numeric_edits: dict[int, QLineEdit] = {}
        self._header: QHeaderView | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        max_col = max(column_kinds) if column_kinds else -1
        for col in range(max_col + 1):
            kind = column_kinds.get(col)
            cell = self._build_cell(col, kind)
            self._cells[col] = cell
            layout.addWidget(cell)
        layout.addStretch(0)

    def _build_cell(self, col: int, kind: TableColumnFilterKind | None) -> QWidget:
        if kind is None:
            spacer = QWidget(self)
            spacer.setFixedWidth(0)
            return spacer
        if kind is TableColumnFilterKind.TEXT:
            edit = QLineEdit(self)
            edit.setPlaceholderText(messages.TABLE_FILTER_TEXT_PLACEHOLDER)
            edit.textChanged.connect(lambda _text: self.filters_changed.emit())
            self._text_edits[col] = edit
            return edit
        if kind is TableColumnFilterKind.BOOL:
            combo = QComboBox(self)
            combo.addItem(messages.TABLE_FILTER_BOOL_ALL, None)
            combo.addItem(messages.FAALWIJZEN_NMF_JA, True)
            combo.addItem(messages.FAALWIJZEN_NMF_NEE, False)
            combo.currentIndexChanged.connect(lambda _idx: self.filters_changed.emit())
            self._bool_combos[col] = combo
            return combo
        edit = QLineEdit(self)
        edit.setPlaceholderText(messages.TABLE_FILTER_NUMERIC_PLACEHOLDER)
        edit.textChanged.connect(lambda _text: self.filters_changed.emit())
        self._numeric_edits[col] = edit
        return edit

    def bind_header(self, header: QHeaderView) -> None:
        self._header = header
        header.sectionResized.connect(self._sync_column_widths)
        header.geometriesChanged.connect(self._sync_column_widths)
        self._sync_column_widths()

    def _sync_column_widths(self, *_args) -> None:
        if self._header is None:
            return
        try:
            header = self._header
            for col, cell in self._cells.items():
                hidden = header.isSectionHidden(col)
                width = 0 if hidden else header.sectionSize(col)
                cell.setVisible(not hidden)
                cell.setFixedWidth(max(width, 0))
        except RuntimeError:
            self._header = None

    def text_value(self, column: int) -> str:
        edit = self._text_edits.get(column)
        return edit.text() if edit is not None else ""

    def bool_value(self, column: int) -> bool | None:
        combo = self._bool_combos.get(column)
        if combo is None:
            return None
        return combo.currentData()

    def numeric_value(self, column: int) -> str:
        edit = self._numeric_edits.get(column)
        return edit.text() if edit is not None else ""

    def clear_all(self) -> None:
        for edit in self._text_edits.values():
            edit.blockSignals(True)
            edit.clear()
            edit.blockSignals(False)
        for combo in self._bool_combos.values():
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
        for edit in self._numeric_edits.values():
            edit.blockSignals(True)
            edit.clear()
            edit.setStyleSheet("")
            edit.blockSignals(False)

    def set_numeric_invalid(self, column: int, invalid: bool) -> None:
        edit = self._numeric_edits.get(column)
        if edit is None:
            return
        edit.setStyleSheet(_FILTER_INVALID_STYLE if invalid else "")

    def apply_invalid_numeric_columns(self, invalid_columns: frozenset[int]) -> None:
        for col in self._numeric_edits:
            self.set_numeric_invalid(col, col in invalid_columns)

    def editor(self, column: int) -> QWidget | None:
        if column in self._text_edits:
            return self._text_edits[column]
        if column in self._bool_combos:
            return self._bool_combos[column]
        if column in self._numeric_edits:
            return self._numeric_edits[column]
        return self._cells.get(column)
