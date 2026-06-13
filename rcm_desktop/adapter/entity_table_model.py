"""Qt-tabelmodel voor schema-gedreven entiteiten-grid (slice 83)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QComboBox, QStyledItemDelegate, QStyleOptionViewItem, QWidget

from rcm_core.models import RCMProject

from rcm_desktop import messages
from rcm_desktop.adapter.entity_cell_display import display_faalwijze_field
from rcm_desktop.adapter.entity_edit_service import EntityEditService, EntityRowView
from rcm_desktop.adapter.tabular_edit_types import CellErrorView
from rcm_desktop.adapter.entity_grid_config import EntityGridViewConfig
from rcm_desktop.adapter.input_search_text import build_row_search_haystack
from rcm_desktop.adapter.entity_grid_derived_values import (
    entity_derived_header,
    entity_derived_value,
)
RAW_ROLE = Qt.UserRole + 1
ERROR_BACKGROUND = QColor(255, 235, 235)
WARNING_BACKGROUND = QColor(255, 235, 156)
WARNING_FOREGROUND = QColor(0, 0, 0)
ERROR_MENU_FOREGROUND = QColor(180, 30, 30)
WARNING_MENU_FOREGROUND = QColor(160, 110, 0)


def menu_foreground_for_severity(severity: str) -> QColor | None:
    if severity == "error":
        return ERROR_MENU_FOREGROUND
    if severity == "warning":
        return WARNING_MENU_FOREGROUND
    return None


def cell_background_for_errors(errs: tuple[CellErrorView, ...]) -> QColor | None:
    if not errs:
        return None
    if any(e.severity == "error" for e in errs):
        return ERROR_BACKGROUND
    return WARNING_BACKGROUND


def cell_foreground_for_errors(errs: tuple[CellErrorView, ...]) -> QColor | None:
    if not errs:
        return None
    if any(e.severity == "error" for e in errs):
        return None
    return WARNING_FOREGROUND


def cell_tooltip_for_errors(errs: tuple[CellErrorView, ...]) -> str | None:
    if not errs:
        return None
    errors = [e.message for e in errs if e.severity == "error"]
    warnings = [e.message for e in errs if e.severity == "warning"]
    parts: list[str] = []
    if errors:
        parts.append("\n".join(errors))
    if warnings:
        parts.append("\n".join(warnings))
    return "\n\n".join(parts)


def apply_findings_style_to_option(option: QStyleOptionViewItem, index: QModelIndex) -> None:
    """Pas foreground/background uit het model toe (dark-theme-delegates negeren dat anders)."""
    fg = index.data(Qt.ForegroundRole)
    if isinstance(fg, QColor):
        option.palette.setColor(QPalette.ColorRole.Text, fg)
        option.palette.setColor(QPalette.ColorRole.HighlightedText, fg)
    bg = index.data(Qt.BackgroundRole)
    if isinstance(bg, QColor):
        option.palette.setColor(QPalette.ColorRole.Base, bg)
        option.palette.setColor(QPalette.ColorRole.Window, bg)

_FAALWIJZEN_HEADERS = {
    "fm_id": messages.FAALWIJZEN_EDIT_HEADER_FM_ID,
    "pbs_id": messages.FAALWIJZEN_EDIT_HEADER_PBS_ID,
    "failure_type": messages.FAALWIJZEN_EDIT_HEADER_FAILURE_TYPE,
    "aging_distribution": messages.FAALWIJZEN_EDIT_HEADER_AGING_DISTRIBUTION,
    "is_evident": messages.FAALWIJZEN_EDIT_HEADER_NMF,
    "faalwijze_omschrijving": messages.FAALWIJZEN_EDIT_HEADER_OMSCHRIJVING,
    "functie_id": messages.FAALWIJZEN_EDIT_HEADER_FUNCTIE,
    "mttf_jaar": messages.FAALWIJZEN_EDIT_HEADER_MTTF,
    "sigma_jaar": messages.FAALWIJZEN_EDIT_HEADER_SIGMA,
    "beta_jaar": messages.FAALWIJZEN_EDIT_HEADER_BETA,
    "repair_quality": messages.FAALWIJZEN_EDIT_HEADER_REPAIR_QUALITY,
    "cost_cm_eur": messages.FAALWIJZEN_EDIT_HEADER_COST_CM,
    "p_ongewenste_gebeurtenis": messages.FAALWIJZEN_EDIT_HEADER_P_EVENT,
}


def _header_for_field(config: EntityGridViewConfig, field: str) -> str:
    if field in config.derived_columns:
        return entity_derived_header(config.view_id, field)
    if config.entity == "faalwijzes":
        return _FAALWIJZEN_HEADERS.get(field, field)
    return field


class EntityTableModel(QAbstractTableModel):
    def __init__(
        self,
        service: EntityEditService,
        project: RCMProject,
        config: EntityGridViewConfig,
        columns: tuple[str, ...],
        *,
        hidden_columns: frozenset[str] = frozenset(),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._project = project
        self._config = config
        self._columns = columns
        self._hidden_columns = hidden_columns
        self._readonly = config.readonly_columns

    def column_ids(self) -> tuple[str, ...]:
        return self._columns

    def visible_column_ids(self) -> tuple[str, ...]:
        return tuple(c for c in self._columns if c not in self._hidden_columns)

    def set_hidden_columns(self, hidden_columns: frozenset[str]) -> None:
        self._hidden_columns = hidden_columns
        if self.rowCount() == 0:
            self.headerDataChanged.emit(Qt.Orientation.Horizontal, 0, len(self._columns) - 1)
            return
        tl = self.index(0, 0)
        br = self.index(self.rowCount() - 1, self.columnCount() - 1)
        self.dataChanged.emit(tl, br, [Qt.DisplayRole])

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self._service.rows())

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self._columns)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and 0 <= section < len(self._columns):
            return _header_for_field(self._config, self._columns[section])
        return super().headerData(section, orientation, role)

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        base = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        field = self._column_field(index.column())
        if field in self._readonly:
            return base
        row_v = self._row_at(index.row())
        if not row_v.editable(field):
            return base
        return base | Qt.ItemIsEditable

    def _row_at(self, row_index: int) -> EntityRowView:
        return self._service.rows()[row_index]

    def row_view_at(self, row_index: int) -> EntityRowView:
        return self._row_at(row_index)

    def search_haystack_at(self, row_index: int) -> str:
        row_v = self._row_at(row_index)
        return build_row_search_haystack(
            self._config,
            self._project,
            row_v.values,
            self.visible_column_ids(),
        )

    def _column_field(self, col: int) -> str:
        return self._columns[col]

    def _errors_on_cell(self, row_v: EntityRowView, field: str) -> tuple[CellErrorView, ...]:
        direct = row_v.field_errors.get(field, ())
        key_field = self._config.key_field
        if field != key_field:
            return direct
        extra: list[CellErrorView] = []
        for hidden_field, errs in row_v.field_errors.items():
            if hidden_field != key_field and hidden_field in self._hidden_columns:
                extra.extend(errs)
        if not extra:
            return direct
        return direct + tuple(extra)

    def row_key_at(self, row_index: int) -> str:
        return self._row_at(row_index).row_key

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row_v = self._row_at(index.row())
        field = self._column_field(index.column())
        value = self._cell_value(row_v, field)

        if role == RAW_ROLE:
            if field == "is_evident" and self._config.entity == "faalwijzes":
                return not bool(value)
            return value

        if role == Qt.EditRole:
            return self._edit_value(row_v, field, value)

        if role == Qt.BackgroundRole:
            return cell_background_for_errors(self._errors_on_cell(row_v, field))

        if role == Qt.ForegroundRole:
            return cell_foreground_for_errors(self._errors_on_cell(row_v, field))

        if role == Qt.ToolTipRole:
            return cell_tooltip_for_errors(self._errors_on_cell(row_v, field))

        if role != Qt.DisplayRole:
            return None

        return self._display_value(row_v, field, value)

    def _cell_value(self, row_v: EntityRowView, field: str) -> Any:
        if field in self._config.derived_columns:
            return entity_derived_value(
                self._config.view_id,
                field,
                self._project,
                row_v.values,
            )
        return row_v.values.get(field)

    def _edit_value(self, row_v: EntityRowView, field: str, value: Any) -> Any:
        if field == "is_evident" and self._config.entity == "faalwijzes":
            return not bool(value)
        if field in ("failure_type", "aging_distribution"):
            return str(value or "")
        if isinstance(value, float):
            if value == int(value):
                return str(int(value))
            return str(value)
        if value is None:
            return ""
        return value

    def _display_value(self, row_v: EntityRowView, field: str, value: Any) -> str:
        if field in self._config.derived_columns:
            if value is None:
                return ""
            if field in ("pm_execution_count_lcc", "pm_first_execution_year"):
                return str(int(value)) if isinstance(value, (int, float)) and float(value) == int(value) else str(value)
            return str(value)
        if self._config.entity == "faalwijzes":
            return display_faalwijze_field(self._project, field, value)
        if value is None:
            return ""
        return str(value)

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole:
            return False
        field = self._column_field(index.column())
        if field in self._config.derived_columns:
            return False
        row_v = self._row_at(index.row())
        if not row_v.editable(field):
            return False
        if field == "is_evident" and self._config.entity == "faalwijzes":
            raw = bool(value)
        elif field in ("failure_type", "aging_distribution"):
            raw = str(value)
        else:
            raw = value if isinstance(value, str) else str(value) if value is not None else ""
        self._service.apply_change(row_v.row_key, field, raw)
        self.dataChanged.emit(
            index,
            index,
            [
                Qt.DisplayRole,
                Qt.EditRole,
                Qt.BackgroundRole,
                Qt.ForegroundRole,
                Qt.ToolTipRole,
                RAW_ROLE,
            ],
        )
        return True

    def emit_grid_refresh(self) -> None:
        if self.rowCount() == 0:
            return
        tl = self.index(0, 0)
        br = self.index(self.rowCount() - 1, self.columnCount() - 1)
        self.dataChanged.emit(
            tl,
            br,
            [
                Qt.DisplayRole,
                Qt.EditRole,
                Qt.BackgroundRole,
                Qt.ForegroundRole,
                Qt.ToolTipRole,
                RAW_ROLE,
            ],
        )


class EntityCellDelegate(QStyledItemDelegate):
    def initStyleOption(self, option: QStyleOptionViewItem, index):  # noqa: ANN001
        super().initStyleOption(option, index)
        apply_findings_style_to_option(option, index)


class EntityFkDelegate(EntityCellDelegate):
    def __init__(self, project: RCMProject, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project = project

    def initStyleOption(self, option: QStyleOptionViewItem, index):  # noqa: ANN001
        super().initStyleOption(option, index)
        from PySide6.QtWidgets import QAbstractItemView

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


class EntityFailureTypeDelegate(EntityCellDelegate):
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


class EntityAgingDistributionDelegate(EntityCellDelegate):
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


class EntityNmfDelegate(EntityCellDelegate):
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


def install_faalwijzen_delegates(table, project: RCMProject, columns: tuple[str, ...]) -> None:
    table.setItemDelegate(EntityCellDelegate(table))
    col = {name: columns.index(name) for name in columns}
    if "functie_id" in col:
        table.setItemDelegateForColumn(col["functie_id"], EntityFkDelegate(project, table))
    if "failure_type" in col:
        table.setItemDelegateForColumn(
            col["failure_type"], EntityFailureTypeDelegate(table)
        )
    if "aging_distribution" in col:
        table.setItemDelegateForColumn(
            col["aging_distribution"], EntityAgingDistributionDelegate(table)
        )
    if "is_evident" in col:
        table.setItemDelegateForColumn(col["is_evident"], EntityNmfDelegate(table))
