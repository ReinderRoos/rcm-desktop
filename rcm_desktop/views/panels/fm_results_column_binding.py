"""FM-resultaten kolomzichtbaarheid — Qt-binding (slice 80)."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu, QTableView

from rcm_desktop.adapter.fm_results_column_policy import (
    FM_OPTIONAL_COLUMN_BY_ID,
    optional_column_indices,
)


def apply_fm_optional_column_visibility(
    table: QTableView,
    *,
    hidden_optional_columns: frozenset[str],
) -> None:
    visibility = optional_column_indices(hidden_optional_columns)
    header = table.horizontalHeader()
    for col_id, col_index in FM_OPTIONAL_COLUMN_BY_ID.items():
        header.setSectionHidden(col_index, not visibility.get(col_id, True))


def build_fm_column_context_menu(
    table: QTableView,
    *,
    hidden_optional_columns: frozenset[str],
    on_toggle: Callable[[str, bool], None],
) -> QMenu:
    menu = QMenu(table)
    visibility = optional_column_indices(hidden_optional_columns)
    for col_id, col_index in sorted(FM_OPTIONAL_COLUMN_BY_ID.items(), key=lambda x: x[1]):
        label = table.model().headerData(col_index, Qt.Orientation.Horizontal)
        action = menu.addAction(str(label))
        action.setCheckable(True)
        action.setChecked(visibility.get(col_id, True))
        action.triggered.connect(lambda checked, cid=col_id: on_toggle(cid, checked))
    return menu
