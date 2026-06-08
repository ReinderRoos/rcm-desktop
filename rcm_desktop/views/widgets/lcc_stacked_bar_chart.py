"""LCC stacked bar chart widget (slice 41)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from rcm_desktop import messages
from rcm_desktop.adapter.lcc_chart_service import LCCYearBucket


class LCCStackedBarChartWidget(QWidget):
    """Gestapelde staafgrafiek per kalenderjaar (correctief + preventief)."""

    year_clicked = Signal(int)

    _CORRECTIEF_COLOR = QColor("#90CAF9")
    _PREVENTIEF_COLOR = QColor("#1565C0")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._buckets: tuple[LCCYearBucket, ...] = ()
        self._selected_year: int | None = None
        self._scale_max: float | None = None
        self.setMinimumHeight(220)

    def set_buckets(self, buckets: tuple[LCCYearBucket, ...]) -> None:
        self._buckets = tuple(buckets)
        self.update()

    def set_selected_year(self, calendar_year: int | None) -> None:
        self._selected_year = calendar_year
        self.update()

    def set_scale_max(self, value: float | None) -> None:
        """Gedeelde Y-schaal voor A/B-vergelijking (slice 56)."""
        self._scale_max = value
        self.update()

    def buckets(self) -> tuple[LCCYearBucket, ...]:
        return self._buckets

    def _layout_metrics(self, rect):
        bottom_axis_height = 18
        left_margin = 8
        right_margin = 8
        n = len(self._buckets)
        usable_w = max(60, rect.width() - left_margin - right_margin)
        slot_w = max(8, usable_w // max(n, 1))
        bar_w = max(4, slot_w - 3)
        plot_h = max(60, rect.height() - bottom_axis_height - 6)
        baseline_y = 6 + plot_h
        return left_margin, right_margin, slot_w, bar_w, plot_h, baseline_y

    def _calendar_year_at(self, x: int, y: int) -> int | None:
        if not self._buckets:
            return None
        rect = self.rect()
        left_margin, _right_margin, slot_w, _bar_w, _plot_h, baseline_y = self._layout_metrics(rect)
        if y < 0 or y > baseline_y + 18:
            return None
        index = (x - left_margin) // slot_w
        if 0 <= index < len(self._buckets):
            return self._buckets[index].calendar_year
        return None

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            year = self._calendar_year_at(int(event.position().x()), int(event.position().y()))
            if year is not None:
                self.year_clicked.emit(year)
        super().mousePressEvent(event)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        painter.fillRect(rect, QColor("#FAFAFA"))
        if not self._buckets:
            painter.setPen(QPen(QColor("#9E9E9E")))
            painter.drawText(rect, Qt.AlignCenter, messages.WORKSPACE_LCC_EMPTY_STATE)
            painter.end()
            return

        local_max = max((b.correctief_eur + b.preventief_eur) for b in self._buckets)
        max_value = (
            self._scale_max
            if self._scale_max is not None and self._scale_max > 0.0
            else local_max
        )
        if max_value <= 0.0:
            painter.setPen(QPen(QColor("#9E9E9E")))
            painter.drawText(rect, Qt.AlignCenter, messages.WORKSPACE_LCC_EMPTY_STATE)
            painter.end()
            return

        left_margin, right_margin, slot_w, bar_w, plot_h, baseline_y = self._layout_metrics(rect)
        text_color = QColor("#212121")
        for i, bucket in enumerate(self._buckets):
            x = left_margin + i * slot_w
            total = bucket.correctief_eur + bucket.preventief_eur
            if total <= 0.0:
                continue
            corr_h = int(plot_h * (bucket.correctief_eur / max_value))
            prev_h = int(plot_h * (bucket.preventief_eur / max_value))
            if bucket.calendar_year == self._selected_year:
                painter.setPen(QPen(QColor("#FF6F00"), 2))
                painter.drawRect(
                    x - 1, baseline_y - corr_h - prev_h - 1, bar_w + 2, corr_h + prev_h + 2
                )
            painter.fillRect(x, baseline_y - corr_h, bar_w, corr_h, QBrush(self._CORRECTIEF_COLOR))
            painter.fillRect(
                x, baseline_y - corr_h - prev_h, bar_w, prev_h, QBrush(self._PREVENTIEF_COLOR)
            )
        painter.setPen(QPen(text_color))
        first_year = self._buckets[0].calendar_year
        last_year = self._buckets[-1].calendar_year
        painter.drawText(left_margin, baseline_y + 14, str(first_year))
        painter.drawText(rect.width() - right_margin - 50, baseline_y + 14, str(last_year))
        painter.end()
