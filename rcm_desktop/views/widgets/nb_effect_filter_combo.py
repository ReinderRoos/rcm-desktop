"""Multi-select dropdown voor NB-effectklassen (slice 71)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics, QMouseEvent, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QComboBox

from rcm_desktop.adapter.view_core_facade import EffectNbFilterSet

from rcm_desktop.adapter.nb_effect_filter_presentation import (
    NbEffectFilterEntry,
    NbEffectFilterPresentation,
)

_MIN_COMBO_WIDTH = 160
_POPUP_EXTRA_WIDTH = 56
_POPUP_MAX_WIDTH = 640


class NbEffectFilterCombo(QComboBox):
    """Checkable combo: lege selectie = alle NB-effecten."""

    filter_changed = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.setReadOnly(True)
        self.setModel(QStandardItemModel(self))
        self.view().pressed.connect(self._on_item_pressed)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.setMinimumWidth(_MIN_COMBO_WIDTH)
        self._updating = False
        self._presentation: NbEffectFilterPresentation | None = None
        self._klassen: tuple[tuple[str, str], ...] = ()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.showPopup()
            event.accept()
            return
        super().mousePressEvent(event)

    def set_klassen(self, klassen: tuple[tuple[str, str], ...]) -> None:
        """Legacy API: bouwt een presentatieplan zonder pruning."""
        self.set_presentation(
            NbEffectFilterPresentation(
                entries=tuple(
                    NbEffectFilterEntry(
                        klasse_id=kid,
                        label=label,
                        selectable=True,
                        disabled_reason=None,
                    )
                    for kid, label in klassen
                )
            )
        )

    def set_presentation(self, presentation: NbEffectFilterPresentation) -> None:
        self._presentation = presentation
        self._klassen = tuple((e.klasse_id, e.label) for e in presentation.entries)
        self._updating = True
        model = self.model()
        assert isinstance(model, QStandardItemModel)
        model.clear()
        for entry in presentation.entries:
            item = QStandardItem(entry.label)
            item.setData(entry.klasse_id, Qt.UserRole)
            item.setToolTip(entry.disabled_reason or entry.label)
            flags = Qt.ItemIsUserCheckable
            if entry.selectable:
                flags |= Qt.ItemIsEnabled
            item.setFlags(flags)
            item.setCheckState(Qt.Unchecked)
            model.appendRow(item)
        self._apply_popup_width(self._klassen)
        self._refresh_label()
        self._updating = False

    def _apply_popup_width(self, klassen: tuple[tuple[str, str], ...]) -> None:
        if not klassen:
            return
        metrics = QFontMetrics(self.view().font())
        longest = max(
            (metrics.horizontalAdvance(label) for _, label in klassen),
            default=0,
        )
        width = min(_POPUP_MAX_WIDTH, max(_MIN_COMBO_WIDTH, longest + _POPUP_EXTRA_WIDTH))
        self.view().setMinimumWidth(width)

    def set_filter(self, filt: EffectNbFilterSet) -> None:
        self._updating = True
        model = self.model()
        assert isinstance(model, QStandardItemModel)
        entry_by_id = (
            {e.klasse_id: e for e in self._presentation.entries}
            if self._presentation is not None
            else {}
        )
        for row in range(model.rowCount()):
            item = model.item(row)
            if item is None:
                continue
            kid = str(item.data(Qt.UserRole))
            checked = not filt.is_all() and kid in filt.selected_klasse_ids
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            entry = entry_by_id.get(kid)
            if entry is not None and not entry.selectable:
                item.setFlags(Qt.ItemIsUserCheckable)
        self._refresh_label()
        self._updating = False

    def current_filter(self) -> EffectNbFilterSet:
        model = self.model()
        assert isinstance(model, QStandardItemModel)
        selected: set[str] = set()
        for row in range(model.rowCount()):
            item = model.item(row)
            if item is not None and item.checkState() == Qt.Checked:
                selected.add(str(item.data(Qt.UserRole)))
        return EffectNbFilterSet(selected_klasse_ids=frozenset(selected))

    def _on_item_pressed(self, index) -> None:
        if self._updating:
            return
        item = self.model().itemFromIndex(index)
        if item is None or not (item.flags() & Qt.ItemIsEnabled):
            return
        item.setCheckState(
            Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
        )
        self._refresh_label()
        self.filter_changed.emit(self.current_filter())

    def _refresh_label(self) -> None:
        filt = self.current_filter()
        if filt.is_all():
            self.setCurrentText("Alle NB-effecten")
            return
        n = len(filt.selected_klasse_ids)
        self.setCurrentText(f"{n} NB-effect(en)")
