"""Slice 75 issue 01 — FM-detail viewport-fit + display-modus Qt-binding."""



from __future__ import annotations



import pytest



pytest.importorskip("PySide6")



from PySide6.QtCore import Qt

from PySide6.QtGui import QStandardItem, QStandardItemModel

from PySide6.QtWidgets import QHeaderView, QStyleOptionViewItem, QTableView



from rcm_desktop.adapter.column_fit_policy import (

    FM_DETAIL_COL_BOUWDEEL,

    FM_DETAIL_COL_FAALWIJZE,

    ColumnFitMode,

)

from rcm_desktop.views.panels.workspace_table_policy import (

    ElideTooltipTableDelegate,

    WordWrapTableDelegate,

    apply_fm_detail_display_mode,

    apply_fm_detail_viewport_fit,

)





@pytest.fixture

def sample_table(qtbot) -> QTableView:

    table = QTableView()

    model = QStandardItemModel(1, 7)

    model.setHorizontalHeaderLabels(

        ["FM-id", "Faalwijze", "PBS-id", "Bouwdeel", "FM", "NB", "Kosten"]

    )

    model.setItem(0, 1, QStandardItem("x" * 120))

    table.setModel(model)

    table.resize(640, 200)

    qtbot.addWidget(table)

    return table





def test_viewport_fit_uses_stretch_on_text_columns(sample_table: QTableView) -> None:

    apply_fm_detail_viewport_fit(sample_table)

    header = sample_table.horizontalHeader()

    assert header.sectionResizeMode(FM_DETAIL_COL_FAALWIJZE) == QHeaderView.Stretch

    assert header.sectionResizeMode(FM_DETAIL_COL_BOUWDEEL) == QHeaderView.Stretch

    assert header.sectionResizeMode(0) == QHeaderView.ResizeToContents

    assert header.stretchLastSection() is False





def test_passend_mode_enables_word_wrap_delegate(sample_table: QTableView) -> None:

    apply_fm_detail_display_mode(sample_table, ColumnFitMode.PASSEND)

    assert sample_table.wordWrap() is True

    assert isinstance(sample_table.itemDelegate(), WordWrapTableDelegate)





def test_passend_delegate_sets_wrap_text_flag(sample_table: QTableView) -> None:

    apply_fm_detail_display_mode(sample_table, ColumnFitMode.PASSEND)

    delegate = sample_table.itemDelegate()

    assert isinstance(delegate, WordWrapTableDelegate)

    index = sample_table.model().index(0, 1)

    option = QStyleOptionViewItem()

    delegate.initStyleOption(option, index)

    assert option.features & QStyleOptionViewItem.ViewItemFeature.WrapText





def test_bijgesneden_mode_disables_word_wrap_and_installs_elide_delegate(

    sample_table: QTableView,

) -> None:

    apply_fm_detail_display_mode(sample_table, ColumnFitMode.BIJGESNEDEN)

    assert sample_table.wordWrap() is False

    assert isinstance(sample_table.itemDelegate(), ElideTooltipTableDelegate)





def test_bijgesneden_delegate_uses_elide_right(sample_table: QTableView) -> None:

    apply_fm_detail_display_mode(sample_table, ColumnFitMode.BIJGESNEDEN)

    delegate = sample_table.itemDelegate()

    assert isinstance(delegate, ElideTooltipTableDelegate)

    index = sample_table.model().index(0, 1)

    option = QStyleOptionViewItem()

    delegate.initStyleOption(option, index)

    assert option.textElideMode == Qt.TextElideMode.ElideRight


