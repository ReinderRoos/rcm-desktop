"""Host-neutraal faalwijzen batch-grid (slice 46)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from rcm_desktop import messages
from rcm_desktop.adapter.entity_edit_service import EntityEditService
from rcm_desktop.adapter.faalwijzen_grid_contract import EDITABLE_FIELDS, SLICE_FIELD_KEYS
from rcm_desktop.adapter.faalwijzen_table_model import (
    FaalwijzenAgingDistributionDelegate,
    FaalwijzenFailureTypeDelegate,
    FaalwijzenFkDelegate,
    FaalwijzenNmfDelegate,
    FaalwijzenTableModel,
)
from rcm_desktop.views.faalwijzen_filter_proxy import FaalwijzenFilterProxy

_BULK_WARN_THRESHOLD = 500


class _BulkApplyDialog(QDialog):
    def __init__(self, parent: QWidget | None, *, field_labels: dict[str, str]) -> None:
        super().__init__(parent)
        self.setWindowTitle(messages.FAALWIJZEN_BULK_DIALOG_TITLE)
        layout = QFormLayout(self)
        self._field = QComboBox()
        for key in sorted(EDITABLE_FIELDS):
            self._field.addItem(field_labels.get(key, key), key)
        self._value = QLineEdit()
        layout.addRow(messages.FAALWIJZEN_BULK_FIELD_LABEL, self._field)
        layout.addRow(messages.FAALWIJZEN_BULK_VALUE_LABEL, self._value)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def field_and_value(self) -> tuple[str, str] | None:
        if self.exec() != QDialog.DialogCode.Accepted:
            return None
        field = str(self._field.currentData())
        return field, self._value.text()


class ValidateFaalwijzenPanel(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(messages.FAALWIJZEN_EDIT_GROUP_TITLE, parent)
        self._service: EntityEditService | None = None
        self._project = None
        self._source_model: FaalwijzenTableModel | None = None
        self._proxy = FaalwijzenFilterProxy(self)

        root = QVBoxLayout(self)
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel(messages.FAALWIJZEN_FILTER_FAILURE_TYPE))
        self._filter_failure = QComboBox()
        self._filter_failure.addItem(messages.FAALWIJZEN_FILTER_ALL, None)
        self._filter_failure.addItem(messages.FAALWIJZEN_FAILURE_RANDOM, "random")
        self._filter_failure.addItem(messages.FAALWIJZEN_FAILURE_AGING, "aging")
        self._filter_failure.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self._filter_failure)

        filter_row.addWidget(QLabel(messages.FAALWIJZEN_FILTER_NMF))
        self._filter_nmf = QComboBox()
        self._filter_nmf.addItem(messages.FAALWIJZEN_FILTER_ALL, None)
        self._filter_nmf.addItem(messages.FAALWIJZEN_NMF_JA, True)
        self._filter_nmf.addItem(messages.FAALWIJZEN_NMF_NEE, False)
        self._filter_nmf.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self._filter_nmf)

        self._search = QLineEdit()
        self._search.setPlaceholderText(messages.FAALWIJZEN_SEARCH_PLACEHOLDER)
        self._search.textChanged.connect(self._proxy.set_search_text)
        filter_row.addWidget(self._search, stretch=1)
        root.addLayout(filter_row)

        bulk_row = QHBoxLayout()
        self._bulk_selection_btn = QPushButton(messages.FAALWIJZEN_BULK_APPLY_SELECTION)
        self._bulk_selection_btn.clicked.connect(self._bulk_on_selection)
        self._bulk_visible_btn = QPushButton(messages.FAALWIJZEN_BULK_APPLY_VISIBLE)
        self._bulk_visible_btn.clicked.connect(self._bulk_on_visible)
        bulk_row.addWidget(self._bulk_selection_btn)
        bulk_row.addWidget(self._bulk_visible_btn)
        bulk_row.addStretch()
        root.addLayout(bulk_row)

        self._table = QTableView()
        self._table.setSortingEnabled(True)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.setSelectionMode(QTableView.ExtendedSelection)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._proxy.setSourceModel(None)
        self._table.setModel(self._proxy)
        root.addWidget(self._table)

        self._field_labels = {
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

    def attach(self, service: EntityEditService, project) -> None:
        self._service = service
        self._project = project
        self._source_model = FaalwijzenTableModel(service, project, parent=self)
        self._proxy.setSourceModel(self._source_model)
        self._table.setModel(self._proxy)
        self._install_delegates()

    def detach(self) -> None:
        self._table.setModel(None)
        self._proxy.setSourceModel(None)
        self._source_model = None
        self._service = None
        self._project = None

    def refresh_view(self) -> None:
        if self._source_model is not None:
            self._source_model.emit_grid_refresh()

    def _install_delegates(self) -> None:
        if self._project is None:
            return
        col = {name: SLICE_FIELD_KEYS.index(name) for name in SLICE_FIELD_KEYS}
        self._table.setItemDelegateForColumn(
            col["functie_id"], FaalwijzenFkDelegate(self._project, self._table)
        )
        self._table.setItemDelegateForColumn(
            col["failure_type"], FaalwijzenFailureTypeDelegate(self._table)
        )
        self._table.setItemDelegateForColumn(
            col["aging_distribution"], FaalwijzenAgingDistributionDelegate(self._table)
        )
        self._table.setItemDelegateForColumn(
            col["is_evident"], FaalwijzenNmfDelegate(self._table)
        )

    def _on_filter_changed(self) -> None:
        self._proxy.set_failure_type_filter(self._filter_failure.currentData())
        nmf = self._filter_nmf.currentData()
        self._proxy.set_nmf_filter(nmf if isinstance(nmf, bool) else None)

    def _selected_fm_ids(self) -> list[str]:
        ids: list[str] = []
        seen: set[str] = set()
        for ix in self._table.selectedIndexes():
            if ix.column() != 0:
                continue
            src_ix = self._proxy.mapToSource(ix)
            src = self._proxy.source_table_model()
            if src is None:
                continue
            fm_id = src.fm_id_at(src_ix.row())
            if fm_id not in seen:
                seen.add(fm_id)
                ids.append(fm_id)
        return ids

    def _bulk_on_selection(self) -> None:
        fm_ids = self._selected_fm_ids()
        if not fm_ids:
            QMessageBox.information(
                self,
                messages.FAALWIJZEN_BULK_DIALOG_TITLE,
                "Selecteer minstens één rij.",
            )
            return
        self._run_bulk(fm_ids)

    def _bulk_on_visible(self) -> None:
        fm_ids = self._proxy.visible_fm_ids()
        if not fm_ids:
            return
        self._run_bulk(fm_ids)

    def _run_bulk(self, fm_ids: list[str]) -> None:
        if self._service is None:
            return
        if len(fm_ids) > _BULK_WARN_THRESHOLD:
            ok = QMessageBox.question(
                self,
                messages.FAALWIJZEN_BULK_DIALOG_TITLE,
                messages.FAALWIJZEN_BULK_LARGE_WARNING.format(count=len(fm_ids)),
            )
            if ok != QMessageBox.StandardButton.Yes:
                return
        dlg = _BulkApplyDialog(self, field_labels=self._field_labels)
        picked = dlg.field_and_value()
        if picked is None:
            return
        field, raw = picked
        result = self._service.apply_bulk_change(fm_ids, field, raw)
        if not result.ok:
            detail = "\n".join(result.errors)
            QMessageBox.warning(
                self,
                messages.FAALWIJZEN_BULK_DIALOG_TITLE,
                messages.FAALWIJZEN_BULK_FAILED.format(detail=detail),
            )
            return
        self.refresh_view()
