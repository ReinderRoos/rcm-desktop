"""Qt table model + delegates over EntityEditService (faalwijzen view)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QStyledItemDelegate, QStyleOptionViewItem, QWidget

from rcm_desktop import messages
from rcm_desktop.adapter.entity_edit_service import EntityEditService, EntityRowView
from rcm_desktop.adapter.faalwijzen_grid_contract import EDITABLE_FIELDS, SLICE_FIELD_KEYS
from rcm_desktop.formatting import format_float
from rcm_core.models import RCMProject

ERROR_BACKGROUND = QColor(255, 235, 235)

_FAILURE_TYPE_LABELS = {
    "random": messages.FAALWIJZEN_FAILURE_RANDOM,
    "aging": messages.FAALWIJZEN_FAILURE_AGING,
}

_AGING_DISTRIBUTION_LABELS = {
    "normal": "Normal",
    "truncated_normal_0": "Links-afgeknipt normal 0+",
    "weibull_2p": "Weibull 2p",
}


def _normalize_display_key(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _nmf_display(is_evident: bool) -> str:
    return messages.FAALWIJZEN_NMF_JA if not is_evident else messages.FAALWIJZEN_NMF_NEE


class FaalwijzenTableModel(QAbstractTableModel):
    _COLUMNS = SLICE_FIELD_KEYS
    _HEADERS = (
        messages.FAALWIJZEN_EDIT_HEADER_FM_ID,
        messages.FAALWIJZEN_EDIT_HEADER_PBS_ID,
        messages.FAALWIJZEN_EDIT_HEADER_FAILURE_TYPE,
        messages.FAALWIJZEN_EDIT_HEADER_AGING_DISTRIBUTION,
        messages.FAALWIJZEN_EDIT_HEADER_NMF,
        messages.FAALWIJZEN_EDIT_HEADER_OMSCHRIJVING,
        messages.FAALWIJZEN_EDIT_HEADER_FUNCTIE,
        messages.FAALWIJZEN_EDIT_HEADER_MTTF,
        messages.FAALWIJZEN_EDIT_HEADER_SIGMA,
        messages.FAALWIJZEN_EDIT_HEADER_BETA,
        messages.FAALWIJZEN_EDIT_HEADER_REPAIR_QUALITY,
        messages.FAALWIJZEN_EDIT_HEADER_COST_CM,
        messages.FAALWIJZEN_EDIT_HEADER_P_EVENT,
    )
    _READONLY_COLS = frozenset({0, 1})

    def __init__(self, service: EntityEditService, project: RCMProject, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self._project = project
        if len(self._HEADERS) != len(self._COLUMNS):
            raise ValueError("Header/column count mismatch in FaalwijzenTableModel")

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
        field = self._column_field(index.column())
        if field not in EDITABLE_FIELDS:
            return base
        return base | Qt.ItemIsEditable

    def _row_at(self, row_index: int) -> EntityRowView:
        rows = self._service.rows()
        return rows[row_index]

    def _field_value(self, row_v: EntityRowView, field: str) -> Any:
        return row_v.values.get(field)

    def _column_field(self, col: int) -> str:
        return self._COLUMNS[col]

    def fm_id_at(self, row_index: int) -> str:
        return self._row_at(row_index).row_key

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

    def _edit_value(self, row_v: EntityRowView, field: str) -> Any:
        if field == "fm_id":
            return row_v.row_key
        if field == "pbs_id":
            return str(row_v.values.get("pbs_id") or "")
        if field == "failure_type":
            return str(row_v.values.get("failure_type") or "random")
        if field == "is_evident":
            return not bool(row_v.values.get("is_evident", True))
        if field == "aging_distribution":
            return str(row_v.values.get("aging_distribution") or "normal")
        if field == "faalwijze_omschrijving":
            return str(row_v.values.get("faalwijze_omschrijving") or "")
        if field == "functie_id":
            return str(row_v.values.get("functie_id") or "")
        if field in {
            "mttf_jaar",
            "sigma_jaar",
            "beta_jaar",
            "repair_quality",
            "cost_cm_eur",
            "p_ongewenste_gebeurtenis",
        }:
            return self._float_edit_string(row_v.values.get(field))
        return None

    def _float_edit_string(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, float) and value == int(value):
            return str(int(value))
        return str(value)

    def _display_value(self, row_v: EntityRowView, field: str) -> str:
        if field == "fm_id":
            return row_v.row_key
        if field == "pbs_id":
            return str(row_v.values.get("pbs_id") or "")
        failure_type = str(row_v.values.get("failure_type") or "random")
        if field == "failure_type":
            return _FAILURE_TYPE_LABELS.get(failure_type, failure_type)
        aging = str(row_v.values.get("aging_distribution") or "normal")
        if field == "aging_distribution":
            return _AGING_DISTRIBUTION_LABELS.get(aging, aging)
        if field == "is_evident":
            return _nmf_display(bool(row_v.values.get("is_evident", True)))
        if field == "faalwijze_omschrijving":
            return str(row_v.values.get("faalwijze_omschrijving") or "")
        if field == "functie_id":
            fid = _normalize_display_key(row_v.values.get("functie_id"))
            if not fid:
                return ""
            fn = self._project.functies.get(fid)
            if fn is None:
                return fid
            return f"{fid} — {fn.functie_omschrijving}"
        for num_field in (
            "mttf_jaar",
            "sigma_jaar",
            "beta_jaar",
            "repair_quality",
            "cost_cm_eur",
            "p_ongewenste_gebeurtenis",
        ):
            if field == num_field:
                val = row_v.values.get(num_field)
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
        if field == "is_evident":
            raw = bool(value)
        elif field in ("failure_type", "aging_distribution"):
            raw = str(value)
        else:
            raw = value if isinstance(value, str) else str(value) if value is not None else ""
        self._service.apply_change(row_v.row_key, field, raw)
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

    def initStyleOption(self, option: QStyleOptionViewItem, index):  # noqa: ANN001
        super().initStyleOption(option, index)
        parent = self.parent()
        if isinstance(parent, QAbstractItemView) and parent.wordWrap():
            option.features |= QStyleOptionViewItem.ViewItemFeature.WrapText

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


class FaalwijzenFailureTypeDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option, index):  # noqa: ANN001
        cb = QComboBox(parent)
        cb.addItem(messages.FAALWIJZEN_FAILURE_RANDOM, "random")
        cb.addItem(messages.FAALWIJZEN_FAILURE_AGING, "aging")
        return cb

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        if not isinstance(editor, QComboBox):
            return
        current = str(index.data(Qt.EditRole) or "random")
        idx = editor.findData(current)
        editor.setCurrentIndex(idx if idx >= 0 else 0)

    def setModelData(self, editor: QWidget, model, index: QModelIndex) -> None:
        if not isinstance(editor, QComboBox):
            return
        model.setData(index, editor.currentData(), Qt.EditRole)


class FaalwijzenAgingDistributionDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option, index):  # noqa: ANN001
        cb = QComboBox(parent)
        cb.addItem("Normal", "normal")
        cb.addItem("Links-afgeknipt normal 0+", "truncated_normal_0")
        cb.addItem("Weibull 2p", "weibull_2p")
        return cb

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        if not isinstance(editor, QComboBox):
            return
        current = str(index.data(Qt.EditRole) or "normal")
        idx = editor.findData(current)
        editor.setCurrentIndex(idx if idx >= 0 else 0)

    def setModelData(self, editor: QWidget, model, index: QModelIndex) -> None:
        if not isinstance(editor, QComboBox):
            return
        model.setData(index, editor.currentData(), Qt.EditRole)


class FaalwijzenNmfDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option, index):  # noqa: ANN001
        cb = QComboBox(parent)
        cb.addItem(messages.FAALWIJZEN_NMF_JA, True)
        cb.addItem(messages.FAALWIJZEN_NMF_NEE, False)
        return cb

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        if not isinstance(editor, QComboBox):
            return
        current = bool(index.data(Qt.EditRole))
        idx = editor.findData(current)
        editor.setCurrentIndex(idx if idx >= 0 else 0)

    def setModelData(self, editor: QWidget, model, index: QModelIndex) -> None:
        if not isinstance(editor, QComboBox):
            return
        nmf_ja = bool(editor.currentData())
        model.setData(index, nmf_ja, Qt.EditRole)
