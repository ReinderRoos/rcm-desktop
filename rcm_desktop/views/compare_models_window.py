"""Vergelijkingswerkruimte — dual-project compare UI (slice 95 issue 07, slice 96)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtGui import QColor
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
from rcm_desktop.adapter.compare_results_service import (
    CompareResultsBundle,
    hydrate_compare_results,
    run_compare_analytical,
)
from rcm_desktop.adapter.compare_session_service import CompareSession, load_compare_session
from rcm_desktop.adapter.compare_visual_presentation_service import build_compare_visual_flags
from rcm_desktop.adapter.compare_workspace_presentation_service import (
    CompareWorkspaceRow,
    build_compare_workspace_view_state,
)
from rcm_desktop.adapter.compare_workspace_table_model import (
    CompareWorkspaceTableModel,
    HIGHLIGHT_ROLE,
    ROW_ROLE,
)
from rcm_desktop.adapter.scenario_compare_chrome import compare_header_stylesheet, scenario_color_hex
from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A, COMPARE_SLOT_B
from rcm_desktop.theme.dp_tokens import DP_WARNING_BG


class CompareModelsWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(messages.COMPARE_MODELS_WINDOW_TITLE)
        self._path_a: Path | None = None
        self._path_b: Path | None = None
        self._compare_session: CompareSession | None = None
        self._results_bundle: CompareResultsBundle | None = None
        self._table_model = CompareWorkspaceTableModel()
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

        run_row = QHBoxLayout()
        self._run_a_button = QPushButton(messages.COMPARE_MODELS_RUN_A)
        self._run_a_button.clicked.connect(lambda: self._run_side("a"))
        run_row.addWidget(self._run_a_button)
        self._run_b_button = QPushButton(messages.COMPARE_MODELS_RUN_B)
        self._run_b_button.clicked.connect(lambda: self._run_side("b"))
        run_row.addWidget(self._run_b_button)
        self._run_both_button = QPushButton(messages.COMPARE_MODELS_RUN_BOTH)
        self._run_both_button.clicked.connect(lambda: self._run_side("both"))
        run_row.addWidget(self._run_both_button)
        run_row.addStretch()
        layout.addLayout(run_row)

        status_row = QHBoxLayout()
        self._run_status_strip = QLabel("")
        self._run_status_a_label = QLabel("A")
        self._run_status_b_label = QLabel("B")
        self._run_status_a_label.setStyleSheet(compare_header_stylesheet(COMPARE_SLOT_A))
        self._run_status_b_label.setStyleSheet(compare_header_stylesheet(COMPARE_SLOT_B))
        status_row.addWidget(self._run_status_a_label)
        status_row.addWidget(self._run_status_strip, stretch=1)
        status_row.addWidget(self._run_status_b_label)
        layout.addLayout(status_row)

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

        self.setCentralWidget(central)
        self.resize(1100, 640)

    def table_model(self) -> CompareWorkspaceTableModel:
        return self._table_model

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
            self._compare_session = session
            self._results_bundle = hydrate_compare_results(session)
            self._refresh_view()
        except Exception as exc:  # noqa: BLE001 — user-facing adapter boundary
            QMessageBox.warning(
                self,
                messages.COMPARE_MODELS_WINDOW_TITLE,
                str(exc),
            )

    def _run_side(self, side: str) -> None:
        if self._compare_session is None:
            return
        self._results_bundle = run_compare_analytical(
            self._compare_session,
            side=side,  # type: ignore[arg-type]
            existing=self._results_bundle,
        )
        self._refresh_view()

    def _refresh_view(self) -> None:
        if self._compare_session is None:
            return
        state = build_compare_workspace_view_state(
            self._compare_session,
            results_bundle=self._results_bundle,
        )
        flags = build_compare_visual_flags(state)
        self._table_model.set_rows(state.rows)
        self._detail_title.setText(
            messages.COMPARE_MODELS_SUMMARY.format(
                label_a=state.label_a,
                label_b=state.label_b,
                count=len(state.rows),
            )
        )
        self._run_status_strip.setText(
            messages.COMPARE_MODELS_RUN_STATUS.format(
                status_a=flags.run_status_text_a,
                status_b=flags.run_status_text_b,
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
            field_rows: tuple[_DiffRow, ...] = ()
            result_rows: tuple[_DiffRow, ...] = ()
        else:
            self._detail_title.setText(
                messages.COMPARE_MODELS_DETAIL_TITLE.format(
                    fm_a=row.fm_id_a or "—",
                    fm_b=row.fm_id_b or "—",
                    klasse=row.difference_class,
                )
            )
            field_rows = tuple(
                _DiffRow(
                    label=diff.field,
                    value_a=_format_value(diff.value_a),
                    value_b=_format_value(diff.value_b),
                    highlight=diff.is_different,
                )
                for diff in row.field_diffs
            )
            result_rows = tuple(
                _DiffRow(
                    label=diff.metric,
                    value_a=_format_value(diff.value_a),
                    value_b=_format_value(diff.value_b),
                    highlight=diff.is_different,
                )
                for diff in row.result_diffs
            )
        field_model = self._field_table.model()
        result_model = self._result_table.model()
        if isinstance(field_model, _DiffTableModel):
            field_model.set_rows(field_rows)
        if isinstance(result_model, _DiffTableModel):
            result_model.set_rows(result_rows)


def _format_value(value: object) -> str:
    if value is None:
        return "—"
    return str(value)


class _DiffRow:
    __slots__ = ("label", "value_a", "value_b", "highlight")

    def __init__(
        self,
        *,
        label: str,
        value_a: str,
        value_b: str,
        highlight: bool,
    ) -> None:
        self.label = label
        self.value_a = value_a
        self.value_b = value_b
        self.highlight = highlight


class _DiffTableModel(QAbstractTableModel):
    def __init__(self, headers: tuple[str, str, str], parent=None) -> None:
        super().__init__(parent)
        self._headers = headers
        self._rows: tuple[_DiffRow, ...] = ()

    def set_rows(self, rows: tuple[_DiffRow, ...]) -> None:
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
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        column = index.column()
        if role == HIGHLIGHT_ROLE:
            return row.highlight
        if role == Qt.BackgroundRole and row.highlight:
            return QColor(DP_WARNING_BG)
        if role == Qt.ForegroundRole:
            if column == 1:
                return QColor(scenario_color_hex(COMPARE_SLOT_A))
            if column == 2:
                return QColor(scenario_color_hex(COMPARE_SLOT_B))
        if role != Qt.DisplayRole:
            return None
        if column == 0:
            return row.label
        if column == 1:
            return row.value_a
        if column == 2:
            return row.value_b
        return None
