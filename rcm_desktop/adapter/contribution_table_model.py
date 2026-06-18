"""Qt-tabelmodel voor `Bijdragen`-rijen.



Toont drie kolommen — categorie, waarde, aandeel-% — voor een lijst

`ContributionRow`. Formattering van de waarde-kolom is afhankelijk van de

actieve metric en NB-weergave (uren vs %).

"""

from __future__ import annotations



from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt



from rcm_desktop import messages

from rcm_desktop.adapter.contribution_chart_service import ContributionRow
from rcm_desktop.adapter.contribution_display_service import format_contribution_value
from rcm_desktop.adapter.results_workspace_state import ContributionPresentation
from rcm_desktop.formatting import format_float



RAW_ROLE = Qt.UserRole + 1



_HEADERS = (

    messages.WORKSPACE_BIJDRAGE_HEADER_CATEGORIE,

    messages.WORKSPACE_BIJDRAGE_HEADER_WAARDE,

    messages.WORKSPACE_BIJDRAGE_HEADER_AANDEEL,

)





class ContributionTableModel(QAbstractTableModel):

    def __init__(

        self,

        rows: tuple[ContributionRow, ...] | list[ContributionRow],

        *,

        metric: str,

        presentation: ContributionPresentation | None = None,

        parent=None,

    ) -> None:

        super().__init__(parent)

        self._rows: tuple[ContributionRow, ...] = tuple(rows)

        self._metric = metric

        self._presentation = presentation or ContributionPresentation()



    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802

        if parent and parent.isValid():

            return 0

        return len(self._rows)



    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802

        if parent and parent.isValid():

            return 0

        return 3



    def headerData(  # noqa: N802

        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole

    ):

        if (

            role == Qt.DisplayRole

            and orientation == Qt.Horizontal

            and 0 <= section < len(_HEADERS)

        ):

            return _HEADERS[section]

        return super().headerData(section, orientation, role)



    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):

        if not index.isValid():

            return None

        row = self._rows[index.row()]

        column = index.column()

        if role == RAW_ROLE:

            if column == 0:

                return row.category_id

            if column == 1:

                return row.value

            if column == 2:

                return row.share_pct

            return None

        if role != Qt.DisplayRole:

            return None

        if column == 0:

            return row.label

        if column == 1:

            return format_contribution_value(
                row.value, self._metric, self._presentation
            )

        if column == 2:

            return f"{format_float(row.share_pct, decimals=1)} %"

        return None


