"""Contribution bar chart widget (slice 41)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from rcm_desktop import messages
from rcm_desktop.adapter.contribution_chart_service import ContributionRow
from rcm_desktop.adapter.contribution_display_service import format_contribution_bar_annotation
from rcm_desktop.adapter.results_workspace_state import (
    ContributionPresentation,
    METRIC_NIET_BESCHIKBAARHEID,
)


class ContributionBarChartWidget(QWidget):
    """Eenvoudige staafgrafiek voor Bijdragen-modus."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: tuple[ContributionRow, ...] = ()
        self._metric: str = METRIC_NIET_BESCHIKBAARHEID
        self._presentation = ContributionPresentation()
        self.setMinimumHeight(180)

    def set_display_context(
        self,
        metric: str,
        presentation: ContributionPresentation,
    ) -> None:
        self._metric = metric
        self._presentation = presentation
        self.update()

    def set_rows(self, rows: tuple[ContributionRow, ...]) -> None:
        self._rows = tuple(rows)
        self.update()

    def rows(self) -> tuple[ContributionRow, ...]:
        return self._rows

    def bar_value_label(self, row: ContributionRow) -> str:
        return format_contribution_bar_annotation(
            row.value, self._metric, self._presentation
        )

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        painter.fillRect(rect, QColor("#FAFAFA"))
        if not self._rows:
            painter.setPen(QPen(QColor("#9E9E9E")))
            painter.drawText(rect, Qt.AlignCenter, messages.WORKSPACE_BIJDRAGE_EMPTY_STATE)
            painter.end()
            return

        max_value = max((r.value for r in self._rows), default=0.0)
        if max_value <= 0.0:
            painter.setPen(QPen(QColor("#9E9E9E")))
            painter.drawText(rect, Qt.AlignCenter, messages.WORKSPACE_BIJDRAGE_EMPTY_STATE)
            painter.end()
            return

        n = len(self._rows)
        bar_height = max(12, (rect.height() - 12) // max(n, 1) - 4)
        bar_color = QColor("#1976D2")
        text_color = QColor("#212121")
        label_width = 220
        right_margin = 8
        for i, row in enumerate(self._rows):
            y = 6 + i * (bar_height + 4)
            painter.setPen(QPen(text_color))
            painter.drawText(6, y + bar_height - 4, row.label[:32])
            bar_x = label_width
            bar_max_width = max(20, rect.width() - bar_x - right_margin - 80)
            bar_w = int(bar_max_width * (row.value / max_value))
            painter.fillRect(bar_x, y, bar_w, bar_height, QBrush(bar_color))
            painter.setPen(QPen(text_color))
            value_label = self.bar_value_label(row)
            painter.drawText(bar_x + bar_w + 4, y + bar_height - 4, value_label)
        painter.end()
