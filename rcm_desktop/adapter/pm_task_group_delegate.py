"""Combo-delegate voor PM ``task_group_id`` in de faalwijze-editor."""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QComboBox, QStyledItemDelegate, QWidget

from rcm_desktop import messages
from rcm_desktop.adapter.fk_normalization import is_empty_fk_key, normalize_optional_fk


class PmTaskGroupDelegate(QStyledItemDelegate):
    def __init__(self, task_group_ids: tuple[str, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._task_group_ids = task_group_ids

    def createEditor(self, parent: QWidget, option, index):  # noqa: ANN001
        cb = QComboBox(parent)
        cb.addItem(messages.FM_EDITOR_TASK_GROUP_NONE, "")
        for gid in self._task_group_ids:
            cb.addItem(gid, gid)
        return cb

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        if not isinstance(editor, QComboBox):
            return
        current = normalize_optional_fk(index.data(Qt.EditRole))
        s = "" if current is None else str(current)
        idx = editor.findData(s)
        editor.setCurrentIndex(idx if idx >= 0 else 0)

    def setModelData(self, editor: QWidget, model, index: QModelIndex) -> None:
        if not isinstance(editor, QComboBox):
            return
        raw = editor.currentData()
        out = "" if raw in (None, "") else str(raw)
        model.setData(index, out, Qt.EditRole)

    def displayText(self, value, locale):  # noqa: ANN001
        if is_empty_fk_key(value):
            return messages.FM_EDITOR_TASK_GROUP_NONE
        return super().displayText(value, locale)
