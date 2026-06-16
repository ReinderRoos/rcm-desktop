"""Gepaard horizontaal staafdiagram voor Faalwijze-analyse compare (slice 102-B2)."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from rcm_desktop import messages
from rcm_desktop.adapter.faalwijze_analyse_service import (
    FaalwijzeComparePresentation,
    FaalwijzeCompareRow,
)
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
)
from rcm_desktop.formatting import format_eur, format_float, format_int
from rcm_desktop.theme.dp_tokens import (
    DP_SCENARIO_1,
    DP_SCENARIO_2,
    DP_TEXT_BODY,
    DP_TEXT_SUBTLE,
    DP_WARNING_BG,
)

_ROW_HEIGHT = 44
_LABEL_WIDTH = 240
_VALUE_WIDTH = 88
_BAR_GAP = 4
_TOP_MARGIN = 8


class FaalwijzeCompareBarChartWidget(QWidget):
    """Full-width gepaarde horizontale balken S1/S2 per faalwijze."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: tuple[FaalwijzeCompareRow, ...] = ()
        self._metric = METRIC_FAALMOMENTEN
        self._content_width = 360
        self.setMinimumWidth(360)
        policy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.setSizePolicy(policy)

    def set_presentation(self, presentation: FaalwijzeComparePresentation) -> None:
        self._rows = tuple(presentation.rows)
        self._metric = presentation.metric
        height = self.preferred_height()
        self.setMinimumHeight(height)
        self.resize(max(self._content_width, self.minimumWidth()), height)
        self.updateGeometry()
        self.update()

    def set_content_width(self, width: int) -> None:
        self._content_width = max(360, width)
        self.resize(self._content_width, max(self.minimumHeight(), self.preferred_height()))
        self.updateGeometry()

    def fm_ids_in_order(self) -> tuple[str, ...]:
        return tuple(row.fm_id for row in self._rows)

    def highlighted_fm_ids(self) -> tuple[str, ...]:
        return tuple(row.fm_id for row in self._rows if row.highlight)

    def active_metric(self) -> str:
        return self._metric

    def scenario_color_s1(self) -> QColor:
        return QColor(DP_SCENARIO_1)

    def scenario_color_s2(self) -> QColor:
        return QColor(DP_SCENARIO_2)

    @staticmethod
    def row_background_color(highlight: bool) -> QColor | None:
        if highlight:
            return QColor(DP_WARNING_BG)
        return None

    def preferred_height(self) -> int:
        if not self._rows:
            return 180
        return max(180, _TOP_MARGIN + len(self._rows) * _ROW_HEIGHT + _TOP_MARGIN)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._content_width, self.preferred_height())

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(360, self.preferred_height())

    def _format_metric(self, value: float | None) -> str:
        if value is None:
            return "—"
        if self._metric == METRIC_FAALMOMENTEN:
            return format_int(int(round(value)))
        if self._metric == METRIC_KOSTEN:
            return format_eur(value)
        return format_float(value)

    def _scale_max(self) -> float:
        values: list[float] = []
        for row in self._rows:
            if row.s1 is not None:
                values.append(row.s1)
            if row.s2 is not None:
                values.append(row.s2)
        return max(values, default=0.0)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        painter.fillRect(rect, QColor("#FAFAFA"))
        if not self._rows:
            painter.setPen(QPen(QColor(DP_TEXT_SUBTLE)))
            painter.drawText(rect, Qt.AlignCenter, messages.WORKSPACE_FM_COMPARE_DIAGRAM_EMPTY)
            painter.end()
            return

        scale_max = self._scale_max()
        if scale_max <= 0.0:
            painter.setPen(QPen(QColor(DP_TEXT_SUBTLE)))
            painter.drawText(rect, Qt.AlignCenter, messages.WORKSPACE_FM_COMPARE_DIAGRAM_EMPTY)
            painter.end()
            return

        bar_area_x = _LABEL_WIDTH + 8
        bar_max_width = max(20, rect.width() - bar_area_x - _VALUE_WIDTH - 12)
        half_bar = max(8, (_ROW_HEIGHT - _BAR_GAP) // 2 - 2)
        text_color = QColor(DP_TEXT_BODY)

        for index, row in enumerate(self._rows):
            y = _TOP_MARGIN + index * _ROW_HEIGHT
            row_rect = rect.adjusted(0, y, 0, -(rect.height() - y - _ROW_HEIGHT))
            bg = self.row_background_color(row.highlight)
            if bg is not None:
                painter.fillRect(row_rect, QBrush(bg))

            label = row.label or row.fm_id
            painter.setPen(QPen(text_color))
            painter.drawText(8, y + half_bar + 4, label[:36])
            if row.bouwdeel_naam:
                painter.setPen(QPen(QColor(DP_TEXT_SUBTLE)))
                painter.drawText(8, y + half_bar + 18, row.bouwdeel_naam[:28])

            s1_y = y + 4
            s2_y = y + 4 + half_bar + _BAR_GAP
            s1_w = 0 if row.s1 is None else int(bar_max_width * (row.s1 / scale_max))
            s2_w = 0 if row.s2 is None else int(bar_max_width * (row.s2 / scale_max))
            painter.fillRect(bar_area_x, s1_y, s1_w, half_bar, QBrush(self.scenario_color_s1()))
            painter.fillRect(bar_area_x, s2_y, s2_w, half_bar, QBrush(self.scenario_color_s2()))
            painter.setPen(QPen(text_color))
            painter.drawText(
                bar_area_x + bar_max_width + 8,
                s1_y + half_bar - 2,
                self._format_metric(row.s1),
            )
            painter.drawText(
                bar_area_x + bar_max_width + 8,
                s2_y + half_bar - 2,
                self._format_metric(row.s2),
            )

        painter.end()
