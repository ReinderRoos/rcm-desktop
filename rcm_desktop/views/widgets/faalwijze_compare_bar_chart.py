"""Gepaard horizontaal staafdiagram voor Faalwijze-analyse compare (slice 102-B2)."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
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
    DP_TEXT_ON_NAVY,
    DP_WARNING_BG,
)

ROW_HEIGHT = 56
_LABEL_WIDTH = 240
_BAR_GAP = 4
_TOP_MARGIN = 8
_VALUE_IN_BAR_MIN_WIDTH = 44
_LABEL_FONT_POINT_SIZE = 10
_VALUE_FONT_POINT_SIZE = 11
_VALUE_LEFT_PAD = 10


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
        return max(180, _TOP_MARGIN + len(self._rows) * ROW_HEIGHT + _TOP_MARGIN)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._content_width, self.preferred_height())

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(360, self.preferred_height())

    def _format_metric(self, value: float | None) -> str:
        if value is None:
            return ""
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

    def _draw_value_label(
        self,
        painter: QPainter,
        *,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        on_bar: bool,
    ) -> None:
        if not text:
            return
        if on_bar and width >= _VALUE_IN_BAR_MIN_WIDTH:
            value_font = QFont(painter.font())
            value_font.setPointSize(_VALUE_FONT_POINT_SIZE)
            value_font.setBold(True)
            painter.setFont(value_font)
            painter.setPen(QPen(QColor(DP_TEXT_ON_NAVY)))
            painter.drawText(
                x + _VALUE_LEFT_PAD,
                y,
                max(0, width - _VALUE_LEFT_PAD),
                height,
                int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                text,
            )
            return
        painter.setPen(QPen(QColor(DP_TEXT_BODY)))
        painter.drawText(
            x + max(width, 0) + 6,
            y,
            120,
            height,
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            text,
        )

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

        label_font = QFont(painter.font())
        label_font.setPointSize(_LABEL_FONT_POINT_SIZE)
        label_font.setBold(False)
        bar_area_x = _LABEL_WIDTH + 8
        bar_max_width = max(20, rect.width() - bar_area_x - 12)
        half_bar = max(12, (ROW_HEIGHT - _BAR_GAP) // 2 - 2)

        for index, row in enumerate(self._rows):
            y = _TOP_MARGIN + index * ROW_HEIGHT
            row_rect = rect.adjusted(0, y, 0, -(rect.height() - y - ROW_HEIGHT))
            bg = self.row_background_color(row.highlight)
            if bg is not None:
                painter.fillRect(row_rect, QBrush(bg))

            label = row.label or row.fm_id
            painter.setFont(label_font)
            painter.setPen(QPen(QColor(DP_TEXT_BODY)))
            painter.drawText(8, y + half_bar + 4, label[:36])
            if row.bouwdeel_naam:
                painter.setPen(QPen(QColor(DP_TEXT_SUBTLE)))
                painter.drawText(8, y + half_bar + 18, row.bouwdeel_naam[:28])

            s1_w = 0 if row.s1 is None else int(bar_max_width * (row.s1 / scale_max))
            s1_text = self._format_metric(row.s1)

            if row.s2 is None:
                bar_h = ROW_HEIGHT - 8
                s1_y = y + 4
                painter.fillRect(
                    bar_area_x, s1_y, s1_w, bar_h, QBrush(self.scenario_color_s1())
                )
                self._draw_value_label(
                    painter,
                    x=bar_area_x,
                    y=s1_y,
                    width=s1_w,
                    height=bar_h,
                    text=s1_text,
                    on_bar=True,
                )
            else:
                s1_y = y + 4
                s2_y = y + 4 + half_bar + _BAR_GAP
                s2_w = int(bar_max_width * (row.s2 / scale_max))
                s2_text = self._format_metric(row.s2)
                painter.fillRect(
                    bar_area_x, s1_y, s1_w, half_bar, QBrush(self.scenario_color_s1())
                )
                painter.fillRect(
                    bar_area_x, s2_y, s2_w, half_bar, QBrush(self.scenario_color_s2())
                )
                self._draw_value_label(
                    painter,
                    x=bar_area_x,
                    y=s1_y,
                    width=s1_w,
                    height=half_bar,
                    text=s1_text,
                    on_bar=True,
                )
                self._draw_value_label(
                    painter,
                    x=bar_area_x,
                    y=s2_y,
                    width=s2_w,
                    height=half_bar,
                    text=s2_text,
                    on_bar=True,
                )

        painter.end()
