"""Table model for one FM compare column in Faalwijze-analyse (slice 102-B1)."""

from __future__ import annotations

from typing import Literal

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from rcm_desktop import messages
from rcm_desktop.adapter.faalwijze_analyse_service import (
    FaalwijzeComparePresentation,
    FaalwijzeCompareRow,
    FaalwijzeCompareSlotCell,
)
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
)
from rcm_desktop.adapter.fm_results_table_model import RAW_ROLE
from rcm_desktop.formatting import format_eur, format_float, format_int
from rcm_desktop.theme.dp_tokens import DP_WARNING_BG

CompareSlotSide = Literal["s1", "s2"]

_BASE_COLUMNS = ("fm_id", "bouwdeel_naam", "label", "metric")
_OPTIONAL_COLUMNS = ("is_nmf", "rf")


class FMCompareTableModel(QAbstractTableModel):
    def __init__(
        self,
        presentation: FaalwijzeComparePresentation,
        *,
        slot_side: CompareSlotSide,
        show_nmf_rf: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._rows = list(presentation.rows)
        self._metric = presentation.metric
        self._slot_side = slot_side
        self._show_nmf_rf = show_nmf_rf

    @property
    def columns(self) -> tuple[str, ...]:
        if self._show_nmf_rf:
            return _BASE_COLUMNS + _OPTIONAL_COLUMNS
        return _BASE_COLUMNS

    def set_show_nmf_rf(self, visible: bool) -> None:
        if visible == self._show_nmf_rf:
            return
        if visible:
            self.beginInsertColumns(QModelIndex(), len(_BASE_COLUMNS), len(_BASE_COLUMNS) + 1)
        else:
            self.beginRemoveColumns(QModelIndex(), len(_BASE_COLUMNS), len(_BASE_COLUMNS) + 1)
        self._show_nmf_rf = visible
        if visible:
            self.endInsertColumns()
        else:
            self.endRemoveColumns()

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        if parent and parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        if parent and parent.isValid():
            return 0
        return len(self.columns)

    def _metric_header(self) -> str:
        if self._metric == METRIC_FAALMOMENTEN:
            return messages.FM_RESULTS_HEADER_FAALMOMENTEN
        if self._metric == METRIC_KOSTEN:
            return messages.FM_RESULTS_HEADER_TOTAL_COST_EUR
        return messages.FM_RESULTS_HEADER_DOWNTIME_HR

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return super().headerData(section, orientation, role)
        col = self.columns[section]
        if col == "fm_id":
            return messages.FM_RESULTS_HEADER_FM_ID
        if col == "bouwdeel_naam":
            return messages.FM_RESULTS_HEADER_BOUWDEEL_NAAM
        if col == "label":
            return messages.FM_RESULTS_HEADER_FAALWIJZE
        if col == "metric":
            return self._metric_header()
        if col == "is_nmf":
            return messages.FM_RESULTS_HEADER_NMF
        if col == "rf":
            return messages.FM_RESULTS_HEADER_RF
        return super().headerData(section, orientation, role)

    def _slot_cell(self, row: FaalwijzeCompareRow) -> FaalwijzeCompareSlotCell:
        return row.s1_cell if self._slot_side == "s1" else row.s2_cell

    def _format_metric(self, value: float | None) -> str:
        if value is None:
            return ""
        if self._metric == METRIC_FAALMOMENTEN:
            return format_int(int(round(value)))
        if self._metric == METRIC_KOSTEN:
            return format_eur(value)
        return format_float(value)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        col = self.columns[index.column()]
        cell = self._slot_cell(row)
        if role == Qt.BackgroundRole and row.highlight:
            return QColor(DP_WARNING_BG)
        if role == RAW_ROLE and col == "fm_id":
            return row.fm_id
        if role != Qt.DisplayRole:
            return None
        if col == "fm_id":
            return row.fm_id
        if col == "bouwdeel_naam":
            return row.bouwdeel_naam
        if col == "label":
            return row.label
        if col == "metric":
            return self._format_metric(cell.metric_value)
        if col == "is_nmf":
            return messages.FM_RESULTS_NMF_YES if cell.is_nmf else ""
        if col == "rf":
            return "" if cell.rf == 0.0 else format_float(cell.rf)
        return None
