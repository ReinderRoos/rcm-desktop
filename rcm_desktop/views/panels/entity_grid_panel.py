"""Generiek schema-gedreven entiteiten-grid (slice 83, filter slice 87)."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from rcm_core.models import RCMProject

from rcm_desktop import messages
from rcm_desktop.adapter.entity_edit_service import EntityEditService
from rcm_desktop.adapter.entity_grid_column_settings import available_column_ids
from rcm_desktop.adapter.entity_grid_config import (
    entity_grid_config_for_view,
    schema_columns_for_view,
)
from rcm_desktop.adapter.entity_table_model import (
    EntityTableModel,
    install_faalwijzen_delegates,
    menu_foreground_for_severity,
)
from rcm_desktop.adapter.input_scope_policy import InputScopeMode, input_scope_mode
from rcm_desktop.views.input_entity_filter_proxy import InputEntityFilterProxy

_SCOPE_ENTITY_LABELS: dict[str, str] = {
    "input.effecten": "effecten",
    "input.taakgroepen": "taakgroepen",
}


class EntityGridPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service: EntityEditService | None = None
        self._project: RCMProject | None = None
        self._view_id: str | None = None
        self._scope_id: str | None = None
        self._hidden_columns: frozenset[str] = frozenset()
        self._source_model: EntityTableModel | None = None
        self._proxy: InputEntityFilterProxy | None = None
        self._on_hidden_columns_changed: Callable[[frozenset[str]], None] | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        self._column_button = QPushButton(messages.WORKSPACE_ENTITY_GRID_COLUMNS)
        self._column_button.clicked.connect(self._show_column_menu)
        toolbar.addWidget(self._column_button)
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText(messages.ENTITY_GRID_SEARCH_PLACEHOLDER)
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self._search_edit, stretch=1)
        self._row_count_label = QLabel()
        toolbar.addWidget(self._row_count_label)
        root.addLayout(toolbar)

        self._scope_status_label = QLabel()
        self._scope_status_label.setVisible(False)
        self._scope_status_label.setStyleSheet("color: palette(mid);")
        root.addWidget(self._scope_status_label)

        self._table = QTableView()
        self._table.setSortingEnabled(True)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.setSelectionMode(QTableView.SingleSelection)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        root.addWidget(self._table)

    def set_hidden_columns_handler(
        self,
        handler: Callable[[frozenset[str]], None] | None,
    ) -> None:
        self._on_hidden_columns_changed = handler

    def attach(
        self,
        service: EntityEditService,
        project: RCMProject,
        *,
        view_id: str,
        hidden_columns: frozenset[str] | None = None,
    ) -> None:
        cfg = entity_grid_config_for_view(view_id)
        if cfg is None:
            raise ValueError(f"Geen grid-config voor view {view_id!r}")
        previous_view = self._view_id
        self._service = service
        self._project = project
        self._view_id = view_id
        self._hidden_columns = (
            hidden_columns if hidden_columns is not None else cfg.optional_columns
        )
        all_columns = schema_columns_for_view(view_id)

        if previous_view != view_id:
            self._search_edit.blockSignals(True)
            self._search_edit.clear()
            self._search_edit.blockSignals(False)

        self._proxy = InputEntityFilterProxy(view_id, parent=self)
        self._source_model = EntityTableModel(
            service,
            project,
            cfg,
            all_columns,
            hidden_columns=self._hidden_columns,
            parent=self,
        )
        self._proxy.setSourceModel(self._source_model)
        self._proxy.set_scope(self._scope_id, project)
        self._proxy.set_search_text(self._search_edit.text())
        self._table.setModel(self._proxy)
        self._apply_column_visibility()
        if cfg.entity == "faalwijzes" and view_id == "input.faalwijzen":
            install_faalwijzen_delegates(self._table, project, all_columns)

        self._update_scope_status()
        self._update_row_count_label()

    def detach(self) -> None:
        self._table.setModel(None)
        if self._proxy is not None:
            self._proxy.setSourceModel(None)
        self._source_model = None
        self._proxy = None
        self._service = None
        self._project = None
        self._view_id = None
        self._scope_status_label.setVisible(False)
        self._row_count_label.clear()

    def set_scope(self, scope_id: str | None, project: RCMProject | None = None) -> None:
        self._scope_id = scope_id
        if project is not None:
            self._project = project
        if self._proxy is not None and self._project is not None:
            self._proxy.set_scope(scope_id, self._project)
        self._update_scope_status()
        self._update_row_count_label()

    def table_model(self) -> EntityTableModel | None:
        return self._source_model

    def row_count(self) -> int:
        if self._source_model is None:
            return 0
        return self._source_model.rowCount()

    def visible_row_count(self) -> int:
        if self._proxy is None:
            return self.row_count()
        return self._proxy.rowCount()

    def set_search_text(self, text: str) -> None:
        self._search_edit.setText(text)

    def search_text(self) -> str:
        return self._search_edit.text()

    def scope_status_text(self) -> str:
        return self._scope_status_label.text()

    def scope_status_visible(self) -> bool:
        return not self._scope_status_label.isHidden()

    def row_count_label_text(self) -> str:
        return self._row_count_label.text()

    def column_menu_action_bold(self, col_id: str) -> bool:
        """Test seam: vet menu-item in het kolommen-menu bij invoerbevindingen."""
        widget = self._column_menu_widget(col_id)
        if isinstance(widget, QCheckBox):
            return widget.font().bold()
        action = self._column_menu_action(col_id)
        return action is not None and action.font().bold()

    def column_menu_action_foreground(self, col_id: str):
        """Test seam: kleur menu-item in het kolommen-menu bij invoerbevindingen."""
        widget = self._column_menu_widget(col_id)
        if isinstance(widget, QCheckBox):
            severity = widget.property("findings_severity")
            if severity in ("error", "warning"):
                return menu_foreground_for_severity(str(severity))
        return None

    def _column_menu_action(self, col_id: str):
        for action in self._build_column_menu().actions():
            if str(action.data()) == col_id:
                return action
        return None

    def _column_menu_widget(self, col_id: str):
        action = self._column_menu_action(col_id)
        if action is None or not isinstance(action, QWidgetAction):
            return None
        return action.defaultWidget()

    def set_hidden_columns(self, hidden: frozenset[str]) -> None:
        self._hidden_columns = hidden
        self._apply_column_visibility()
        if self._on_hidden_columns_changed is not None and self._view_id is not None:
            self._on_hidden_columns_changed(self._hidden_columns)

    def refresh_view(self) -> None:
        if self._service is not None:
            self._service.refresh_rows()
        if self._source_model is not None:
            self._source_model.emit_grid_refresh()
        self._update_row_count_label()

    def _apply_column_visibility(self) -> None:
        if self._source_model is None:
            return
        self._source_model.set_hidden_columns(self._hidden_columns)
        for i, col_id in enumerate(self._source_model.column_ids()):
            self._table.setColumnHidden(i, col_id in self._hidden_columns)
        if self._proxy is not None:
            self._proxy.set_search_text(self._search_edit.text())

    def _on_search_changed(self, text: str) -> None:
        if self._proxy is not None:
            self._proxy.set_search_text(text)
        self._update_row_count_label()

    def _update_row_count_label(self) -> None:
        visible = self.visible_row_count()
        total = self.row_count()
        text = messages.ENTITY_GRID_ROW_COUNT.format(visible=visible, total=total)
        if self._service is not None:
            error_count, warning_count = self._service.findings_count()
            if error_count or warning_count:
                text += messages.ENTITY_GRID_FINDINGS_SUFFIX.format(
                    errors=error_count,
                    warnings=warning_count,
                )
        self._row_count_label.setText(text)

    def _update_scope_status(self) -> None:
        if self._view_id is None or self._scope_id is None:
            self._scope_status_label.setVisible(False)
            return
        try:
            mode = input_scope_mode(self._view_id)
        except ValueError:
            self._scope_status_label.setVisible(False)
            return
        if mode != InputScopeMode.PROJECT_WIDE:
            self._scope_status_label.setVisible(False)
            return
        entity_label = _SCOPE_ENTITY_LABELS.get(self._view_id, "rijen")
        self._scope_status_label.setText(
            messages.ENTITY_GRID_SCOPE_NOT_APPLICABLE.format(entity=entity_label)
        )
        self._scope_status_label.setVisible(True)

    def _build_column_menu(self) -> QMenu:
        menu = QMenu(self)
        if self._view_id is None or self._service is None:
            return menu
        bold_font = QFont()
        bold_font.setBold(True)
        severity_by_col = self._service.column_findings_severity()
        for col_id in schema_columns_for_view(self._view_id):
            severity = severity_by_col.get(col_id)
            if severity is None:
                action = menu.addAction(col_id)
                action.setCheckable(True)
                action.setChecked(col_id not in self._hidden_columns)
                action.setData(col_id)
                continue

            cb = QCheckBox(col_id)
            cb.setChecked(col_id not in self._hidden_columns)
            cb.setFont(bold_font)
            cb.setProperty("findings_severity", severity)
            fg = menu_foreground_for_severity(severity)
            if fg is not None:
                cb.setStyleSheet(
                    f"QCheckBox {{ color: rgb({fg.red()}, {fg.green()}, {fg.blue()}); font-weight: bold; }}"
                )
            wa = QWidgetAction(menu)
            wa.setData(col_id)
            wa.setDefaultWidget(cb)
            menu.addAction(wa)
        return menu

    def _show_column_menu(self) -> None:
        if self._view_id is None or self._service is None or self._project is None:
            return
        cfg = entity_grid_config_for_view(self._view_id)
        if cfg is None:
            return
        menu = self._build_column_menu()
        chosen = menu.exec(self._column_button.mapToGlobal(self._column_button.rect().bottomLeft()))
        if chosen is None:
            return
        col_id = str(chosen.data())
        if col_id not in available_column_ids(self._view_id):
            return
        widget = chosen.defaultWidget()
        is_checked = widget.isChecked() if isinstance(widget, QCheckBox) else chosen.isChecked()
        hidden = set(self._hidden_columns)
        if is_checked:
            hidden.discard(col_id)
        else:
            hidden.add(col_id)
        self.set_hidden_columns(frozenset(hidden))
