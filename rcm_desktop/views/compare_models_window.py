"""Vergelijkingswerkruimte — dual-project compare UI (slice 95 issue 07)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from rcm_desktop import messages
from rcm_desktop.adapter.compare_balanced_presentation_service import build_compare_presentation
from rcm_desktop.adapter.compare_session_service import CompareSession, load_compare_session
from rcm_desktop.adapter.normalization_proposal_service import build_normalization_proposals
from rcm_desktop.adapter.normalization_review_presentation_service import (
    build_normalization_review_presentation,
)
from rcm_desktop.adapter.normalization_review_table_model import NormalizationReviewTableModel
from rcm_desktop.adapter.patch_audit_service import (
    AuditTrail,
    apply_approved_normalization,
    rollback_last_patch,
)
from rcm_desktop.adapter.tabular_edit_types import MaterializeBlockedError
from rcm_desktop.adapter.compare_workspace_presentation_service import (
    CompareWorkspaceRow,
    build_compare_workspace_view_state,
)
from rcm_desktop.adapter.compare_workspace_table_model import (
    CompareWorkspaceTableModel,
    ROW_ROLE,
)


class CompareModelsWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(messages.COMPARE_MODELS_WINDOW_TITLE)
        self._path_a: Path | None = None
        self._path_b: Path | None = None
        self._compare_session: CompareSession | None = None
        self._normalization_proposal_items: tuple = ()
        self._audit_trail = AuditTrail()
        self._table_model = CompareWorkspaceTableModel()
        self._normalization_model = NormalizationReviewTableModel(self)
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget(self)
        layout = QVBoxLayout(central)

        form = QFormLayout()
        path_a_row = QHBoxLayout()
        self._path_a_edit = QLineEdit()
        self._path_a_edit.setReadOnly(True)
        browse_a = QPushButton("…")
        browse_a.clicked.connect(self._browse_a)
        path_a_row.addWidget(self._path_a_edit)
        path_a_row.addWidget(browse_a)
        form.addRow(messages.COMPARE_MODELS_PATH_A, path_a_row)

        path_b_row = QHBoxLayout()
        self._path_b_edit = QLineEdit()
        self._path_b_edit.setReadOnly(True)
        browse_b = QPushButton("…")
        browse_b.clicked.connect(self._browse_b)
        path_b_row.addWidget(self._path_b_edit)
        path_b_row.addWidget(browse_b)
        form.addRow(messages.COMPARE_MODELS_PATH_B, path_b_row)
        layout.addLayout(form)

        load_row = QHBoxLayout()
        load_row.addStretch()
        self._load_button = QPushButton(messages.COMPARE_MODELS_LOAD_BUTTON)
        self._load_button.clicked.connect(self._load_compare)
        load_row.addWidget(self._load_button)
        layout.addLayout(load_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self._fm_table = QTableView()
        self._fm_table.setModel(self._table_model)
        self._fm_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._fm_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._fm_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._fm_table.selectionModel().selectionChanged.connect(self._on_row_selected)
        splitter.addWidget(self._fm_table)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        self._detail_title = QLabel(messages.COMPARE_MODELS_DETAIL_PLACEHOLDER)
        detail_layout.addWidget(self._detail_title)

        self._field_table = QTableView()
        self._field_table.setModel(_DiffTableModel(messages.COMPARE_MODELS_DETAIL_FIELD_HEADER))
        self._field_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        detail_layout.addWidget(self._field_table)

        self._result_table = QTableView()
        self._result_table.setModel(_DiffTableModel(messages.COMPARE_MODELS_DETAIL_RESULT_HEADER))
        self._result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        detail_layout.addWidget(self._result_table)
        splitter.addWidget(detail)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter)

        norm_title = QLabel(messages.NORMALIZATION_REVIEW_TITLE)
        layout.addWidget(norm_title)
        self._normalization_table = QTableView()
        self._normalization_table.setModel(self._normalization_model)
        self._normalization_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self._normalization_table)

        norm_actions = QHBoxLayout()
        self._normalization_apply_button = QPushButton(messages.NORMALIZATION_REVIEW_APPLY)
        self._normalization_apply_button.clicked.connect(self._apply_normalization)
        norm_actions.addWidget(self._normalization_apply_button)
        self._normalization_rollback_button = QPushButton(messages.NORMALIZATION_REVIEW_ROLLBACK)
        self._normalization_rollback_button.clicked.connect(self._rollback_normalization)
        norm_actions.addWidget(self._normalization_rollback_button)
        norm_actions.addStretch(1)
        self._normalization_audit_label = QLabel("")
        norm_actions.addWidget(self._normalization_audit_label)
        layout.addLayout(norm_actions)

        self.setCentralWidget(central)
        self.resize(1100, 640)

    def table_model(self) -> CompareWorkspaceTableModel:
        return self._table_model

    def normalization_model(self) -> NormalizationReviewTableModel:
        return self._normalization_model

    def path_a_label(self) -> str:
        return self._path_a.name if self._path_a is not None else ""

    def path_b_label(self) -> str:
        return self._path_b.name if self._path_b is not None else ""

    def load_paths(self, path_a: Path | str, path_b: Path | str) -> None:
        self._path_a = Path(path_a)
        self._path_b = Path(path_b)
        self._path_a_edit.setText(str(self._path_a))
        self._path_b_edit.setText(str(self._path_b))
        self._load_compare()

    def _browse_a(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            messages.COMPARE_MODELS_PATH_A,
            "",
            "RCM JSON (*.rcm.json);;JSON (*.json)",
        )
        if path:
            self._path_a = Path(path)
            self._path_a_edit.setText(path)

    def _browse_b(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            messages.COMPARE_MODELS_PATH_B,
            "",
            "RCM JSON (*.rcm.json);;JSON (*.json)",
        )
        if path:
            self._path_b = Path(path)
            self._path_b_edit.setText(path)

    def _load_compare(self) -> None:
        if self._path_a is None or self._path_b is None:
            QMessageBox.information(
                self,
                messages.COMPARE_MODELS_WINDOW_TITLE,
                messages.COMPARE_MODELS_SELECT_BOTH,
            )
            return
        try:
            session = load_compare_session(self._path_a, self._path_b)
            state = build_compare_workspace_view_state(session)
            self._compare_session = session
            self._load_normalization_review(session)
        except Exception as exc:  # noqa: BLE001 — user-facing adapter boundary
            QMessageBox.warning(
                self,
                messages.COMPARE_MODELS_WINDOW_TITLE,
                str(exc),
            )
            return
        self._table_model.set_rows(state.rows)
        self._detail_title.setText(
            messages.COMPARE_MODELS_SUMMARY.format(
                label_a=state.label_a,
                label_b=state.label_b,
                count=len(state.rows),
            )
        )
        if state.rows:
            self._fm_table.selectRow(0)
            self._show_row_detail(state.rows[0])
        else:
            self._show_row_detail(None)

    def _on_row_selected(self) -> None:
        indexes = self._fm_table.selectionModel().selectedRows()
        if not indexes:
            self._show_row_detail(None)
            return
        row = self._table_model.data(indexes[0], ROW_ROLE)
        if isinstance(row, CompareWorkspaceRow):
            self._show_row_detail(row)

    def _show_row_detail(self, row: CompareWorkspaceRow | None) -> None:
        if row is None:
            self._detail_title.setText(messages.COMPARE_MODELS_DETAIL_PLACEHOLDER)
            field_rows: tuple[tuple[str, str, str], ...] = ()
            result_rows: tuple[tuple[str, str, str], ...] = ()
        else:
            self._detail_title.setText(
                messages.COMPARE_MODELS_DETAIL_TITLE.format(
                    fm_a=row.fm_id_a or "—",
                    fm_b=row.fm_id_b or "—",
                    klasse=row.difference_class,
                )
            )
            field_rows = tuple(
                (diff.field, _format_value(diff.value_a), _format_value(diff.value_b))
                for diff in row.field_diffs
            )
            result_rows = tuple(
                (diff.metric, _format_value(diff.value_a), _format_value(diff.value_b))
                for diff in row.result_diffs
            )
        field_model = self._field_table.model()
        result_model = self._result_table.model()
        if isinstance(field_model, _DiffTableModel):
            field_model.set_rows(field_rows)
        if isinstance(result_model, _DiffTableModel):
            result_model.set_rows(result_rows)

    def _load_normalization_review(self, session: CompareSession) -> None:
        presentation = build_compare_presentation(session.project_a, session.project_b)
        proposals = build_normalization_proposals(presentation, direction="a_to_b")
        self._normalization_proposal_items = proposals.items
        review = build_normalization_review_presentation(proposals)
        self._normalization_model.set_presentation(review)
        self._normalization_audit_label.setText("")

    def _apply_normalization(self) -> None:
        if self._compare_session is None or not self._normalization_proposal_items:
            return
        approved = self._normalization_model.approved_indices()
        if not approved:
            QMessageBox.information(
                self,
                messages.NORMALIZATION_REVIEW_TITLE,
                messages.NORMALIZATION_REVIEW_NO_APPROVED,
            )
            return
        try:
            updated, audit = apply_approved_normalization(
                self._compare_session.project_a,
                self._normalization_proposal_items,
                approved_indices=approved,
            )
        except MaterializeBlockedError as exc:
            QMessageBox.warning(
                self,
                messages.NORMALIZATION_REVIEW_TITLE,
                str(exc),
            )
            return
        self._compare_session = CompareSession(
            path_a=self._compare_session.path_a,
            path_b=self._compare_session.path_b,
            project_a=updated,
            project_b=self._compare_session.project_b,
        )
        self._audit_trail.entries.extend(audit.entries)
        self._normalization_audit_label.setText(
            messages.NORMALIZATION_REVIEW_AUDIT.format(count=self._audit_trail.patch_count)
        )

    def _rollback_normalization(self) -> None:
        if self._compare_session is None or not self._audit_trail.entries:
            return
        restored = rollback_last_patch(self._compare_session.project_a, self._audit_trail)
        self._compare_session = CompareSession(
            path_a=self._compare_session.path_a,
            path_b=self._compare_session.path_b,
            project_a=restored,
            project_b=self._compare_session.project_b,
        )
        self._normalization_audit_label.setText(
            messages.NORMALIZATION_REVIEW_AUDIT.format(count=self._audit_trail.patch_count)
        )


def _format_value(value: object) -> str:
    if value is None:
        return "—"
    return str(value)


class _DiffTableModel(QAbstractTableModel):
    def __init__(self, headers: tuple[str, str, str], parent=None) -> None:
        super().__init__(parent)
        self._headers = headers
        self._rows: tuple[tuple[str, str, str], ...] = ()

    def set_rows(self, rows: tuple[tuple[str, str, str], ...]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent=None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent=None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return 3

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # noqa: N802
        if orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return super().headerData(section, orientation, role)
        if section < 0 or section >= len(self._headers):
            return None
        return self._headers[section]

    def data(self, index, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        row = self._rows[index.row()]
        return row[index.column()]
