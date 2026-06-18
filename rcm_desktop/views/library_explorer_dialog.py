"""Library explorer dialoog — N-bronnen badge + variant clusters (slice 64 issue 04)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from rcm_desktop.adapter.view_core_facade import RCMProject
from rcm_desktop import messages
from rcm_desktop.adapter.library_explorer_service import (
    LibraryExplorerRow,
    build_library_explorer_rows,
)


class LibraryExplorerDialog(QDialog):
    """Toon portfolio-bibliotheek met provenance-badges."""

    def __init__(self, project: RCMProject, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list[LibraryExplorerRow] = build_library_explorer_rows(project.bibliotheek)

        self.setWindowTitle(messages.LIBRARY_EXPLORER_TITLE)
        layout = QVBoxLayout(self)

        intro = QLabel(messages.LIBRARY_EXPLORER_INTRO)
        intro.setWordWrap(True)
        layout.addWidget(intro)

        headers = messages.LIBRARY_EXPLORER_HEADERS
        self._table = QTableWidget(len(self._rows), len(headers))
        self._table.setHorizontalHeaderLabels(list(headers))
        for idx, row in enumerate(self._rows):
            variant_label = "ja" if row.variant_cluster else ""
            for col, text in enumerate(
                (row.omschrijving, row.categorie, row.bron_badge, variant_label, row.waarde)
            ):
                self._table.setItem(idx, col, QTableWidgetItem(text))
        self._table.resizeColumnsToContents()
        layout.addWidget(self._table)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def row_count(self) -> int:
        return len(self._rows)

    def bron_badge_at(self, row: int) -> str:
        return self._rows[row].bron_badge
