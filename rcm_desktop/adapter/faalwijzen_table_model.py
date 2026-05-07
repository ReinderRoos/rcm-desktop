"""Qt table model + delegates over FaalwijzenEditService."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QComboBox, QStyledItemDelegate, QWidget

from rcm_desktop import messages
from rcm_desktop.adapter.faalwijzen_edit_service import (
    EDITABLE_FIELDS,
    FaalwijzenEditService,
    FaalwijzenRowView,
    SLICE_FIELD_KEYS,
)
from rcm_desktop.formatting import format_float
from rcm_core.models import RCMProject

ERROR_BACKGROUND = QColor(255, 235, 235)


def _normalize_display_key(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


class FaalwijzenTableModel(QAbstractTableModel):
    _COLUMNS = SLICE_FIELD_KEYS
    _HEADERS = (
        messages.FAALWIJZEN_EDIT_HEADER_FM_ID,
        messages.FAALWIJZEN_EDIT_HEADER_PBS_ID,
        messages.FAALWIJZEN_EDIT_HEADER_OMSCHRIJVING,
        messages.FAALWIJZEN_EDIT_HEADER_FUNCTIE,
        messages.FAALWIJZEN_EDIT_HEADER_MTTF,
        messages.FAALWIJZEN_EDIT_HEADER_SIGMA,
        messages.FAALWIJZEN_EDIT_HEADER_COST_CM,
        messages.FAALWIJZEN_EDIT_HEADER_P_EVENT,
    )
    _READONLY_COLS = frozenset({0, 1})

    def __init__(self, service: FaalwijzenEditService, project: RCMProject, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self._project = project

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self._service.rows())

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self._COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and 0 <= section < len(self._HEADERS):
            return self._HEADERS[section]
        return super().headerData(section, orientation, role)

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        base = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() in self._READONLY_COLS:
            return base
        return base | Qt.ItemIsEditable

    def _row_at(self, row_index: int) -> FaalwijzenRowView:
        rows = self._service.rows()
        return rows[row_index]

    def _column_field(self, col: int) -> str:
        return self._COLUMNS[col]

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row_v = self._row_at(index.row())
        field = self._column_field(index.column())

        if role == Qt.EditRole:
            return self._edit_value(row_v, field)

        if role == Qt.BackgroundRole:
            errs = row_v.field_errors.get(field)
            if errs:
                return ERROR_BACKGROUND
            return None

        if role == Qt.ToolTipRole:
            errs = row_v.field_errors.get(field)
            if errs:
                return errs[0].message
            return None

        if role != Qt.DisplayRole:
            return None

        return self._display_value(row_v, field)

    def _edit_value(self, row_v: FaalwijzenRowView, field: str) -> Any:
        if field == "fm_id":
            return row_v.fm_id
        if field == "pbs_id":
            return row_v.pbs_id
        if field == "faalwijze_omschrijving":
            return row_v.faalwijze_omschrijving
        if field == "functie_id":
            return row_v.functie_id
        if field == "mttf_jaar":
            return self._float_edit_string(row_v.mttf_jaar)
        if field == "sigma_jaar":
            return self._float_edit_string(row_v.sigma_jaar)
        if field == "cost_cm_eur":
            return self._float_edit_string(row_v.cost_cm_eur)
        if field == "p_ongewenste_gebeurtenis":
            return self._float_edit_string(row_v.p_ongewenste_gebeurtenis)
        return None

    def _float_edit_string(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, float) and value == int(value):
            return str(int(value))
        return str(value)

    def _display_value(self, row_v: FaalwijzenRowView, field: str) -> str:
        if field == "fm_id":
            return row_v.fm_id
        if field == "pbs_id":
            return row_v.pbs_id
        if field == "faalwijze_omschrijving":
            return row_v.faalwijze_omschrijving
        if field == "functie_id":
            fid = _normalize_display_key(row_v.functie_id)
            if not fid:
                return ""
            fn = self._project.functies.get(fid)
            if fn is None:
                return fid
            return f"{fid} — {fn.functie_omschrijving}"
        for num_field in ("mttf_jaar", "sigma_jaar", "cost_cm_eur", "p_ongewenste_gebeurtenis"):
            if field == num_field:
                val = getattr(row_v, field)
                if val is None:
                    return ""
                try:
                    return format_float(float(val))
                except (TypeError, ValueError):
                    return str(val)
        return ""

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole:
            return False
        field = self._column_field(index.column())
        if field not in EDITABLE_FIELDS:
            return False
        row_v = self._row_at(index.row())
        raw = value if isinstance(value, str) else str(value) if value is not None else ""
        self._service.apply_change(row_v.fm_id, field, raw)
        return True

    def emit_grid_refresh(self) -> None:
        if self.rowCount() == 0:
            return
        tl = self.index(0, 0)
        br = self.index(self.rowCount() - 1, self.columnCount() - 1)
        self.dataChanged.emit(
            tl,
            br,
            [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole, Qt.ToolTipRole],
        )


class FaalwijzenFkDelegate(QStyledItemDelegate):
    """Combo editor with empty choice plus ``id — omschrijving`` entries."""

    def __init__(self, project: RCMProject, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project = project

    def createEditor(self, parent: QWidget, option, index):  # noqa: ANN001
        cb = QComboBox(parent)
        cb.addItem("", "")
        for fid in sorted(self._project.functies.keys()):
            fn = self._project.functies[fid]
            cb.addItem(f"{fid} — {fn.functie_omschrijving}", fid)
        return cb

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        if not isinstance(editor, QComboBox):
            return
        current = index.data(Qt.EditRole)
        s = str(current or "").strip()
        idx = editor.findData(s)
        editor.setCurrentIndex(idx if idx >= 0 else 0)

    def setModelData(self, editor: QWidget, model, index: QModelIndex) -> None:
        if not isinstance(editor, QComboBox):
            return
        fid = editor.currentData()
        out = "" if fid in (None, "") else str(fid)
        model.setData(index, out, Qt.EditRole)
