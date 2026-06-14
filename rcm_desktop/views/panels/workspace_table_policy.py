"""Gedeelde tabel-header policy voor resultatenwerkruimte-panelen."""



from __future__ import annotations



from PySide6.QtCore import QEvent, Qt

from PySide6.QtWidgets import (

    QHeaderView,

    QStyledItemDelegate,

    QStyleOptionViewItem,

    QTableView,

    QToolTip,

)



from rcm_desktop.adapter.column_fit_policy import (

    ColumnFitMode,

    decide_column_fit,

    is_stretch_column,

)

from rcm_desktop.table_columns import resize_table_view_rows_if_wrapped

from rcm_desktop.table_ui_constants import ROW_RESIZE_MAX_ROWS_FM_RESULTS





def apply_workspace_data_table_header_policy(header: QHeaderView) -> None:

    """Schaalbare kolombreedtes i.p.v. ResizeToContents op grote tabellen (slice 25)."""

    header.setSectionResizeMode(QHeaderView.Interactive)

    header.setStretchLastSection(True)





class WordWrapTableDelegate(QStyledItemDelegate):

    """Celtekst over meerdere regels (slice 75)."""



    def initStyleOption(self, option: QStyleOptionViewItem, index) -> None:  # type: ignore[no-untyped-def]

        super().initStyleOption(option, index)

        option.features |= QStyleOptionViewItem.ViewItemFeature.WrapText





class ElideTooltipTableDelegate(QStyledItemDelegate):

    """Enkele regel met elide en volledige tekst in tooltip (slice 75)."""



    def initStyleOption(self, option: QStyleOptionViewItem, index) -> None:  # type: ignore[no-untyped-def]

        super().initStyleOption(option, index)

        option.textElideMode = Qt.ElideRight



    def helpEvent(self, event, view, option, index):  # type: ignore[no-untyped-def]

        if event.type() == QEvent.Type.ToolTip:

            tip = index.data(Qt.ItemDataRole.ToolTipRole)

            if tip:

                QToolTip.showText(event.globalPos(), str(tip), view)

                return True

            text = index.data(Qt.ItemDataRole.DisplayRole)

            if text:

                QToolTip.showText(event.globalPos(), str(text), view)

                return True

        return super().helpEvent(event, view, option, index)





def apply_fm_detail_viewport_fit(table: QTableView) -> None:

    """Verdeel kolombreedtes binnen de viewport: Stretch op tekst, inhoud op rest."""

    header = table.horizontalHeader()

    column_count = header.count()

    header.setStretchLastSection(False)

    for col in range(column_count):

        if is_stretch_column(col):

            header.setSectionResizeMode(col, QHeaderView.Stretch)

        else:

            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)





def apply_fm_detail_display_mode(table: QTableView, mode: ColumnFitMode) -> None:

    """Pas viewport-autofit en regelomloop toe op de FM-detail-tabel."""

    decision = decide_column_fit(mode)

    apply_fm_detail_viewport_fit(table)

    table.setWordWrap(decision.word_wrap)

    if decision.word_wrap:

        table.setItemDelegate(WordWrapTableDelegate(table))

        resize_table_view_rows_if_wrapped(

            table,

            wrapped=True,

            max_rows=ROW_RESIZE_MAX_ROWS_FM_RESULTS,

        )

        return

    table.setItemDelegate(ElideTooltipTableDelegate(table))

    table.resizeRowsToContents()





def apply_column_fit_mode_to_table(table: QTableView, mode: ColumnFitMode) -> None:

    """Compat-alias voor FM-detail weergave (slice 75)."""

    apply_fm_detail_display_mode(table, mode)


