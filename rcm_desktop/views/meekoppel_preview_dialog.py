"""Selectiedialoog meekoppel-preview (slice 54, v2 workflow)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from rcm_desktop import messages
from rcm_desktop.adapter.meekoppel_apply_service import MeekoppelAnchor, MeekoppelLocationPreview
from rcm_desktop.adapter.meekoppel_bundle_insight_service import BundleScopeKind
from rcm_desktop.adapter.meekoppel_display_service import due_calendar_year
from rcm_desktop.adapter.meekoppel_preview_selection_service import (
    MeekoppelPreviewSelectionModel,
    is_shiftable,
)
from rcm_desktop.adapter.meekoppelkansen_discovery_service import MeekoppelLocationGroup
from rcm_desktop.adapter.meekoppel_workflow_service import MeekoppelWorkflowService
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.project_session import ProjectSession


@dataclass(frozen=True)
class MeekoppelPreviewDialogResult:
    accepted: bool
    preview: MeekoppelLocationPreview | None
    scope_kind: BundleScopeKind | None
    checked_pm_ids: frozenset[str]


class MeekoppelPreviewDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        *,
        session: ProjectSession,
        overlay: PlanningOverlayState,
        pbs_ids: frozenset[str],
        anchor: MeekoppelAnchor,
        location_group: MeekoppelLocationGroup | None,
        workflow: MeekoppelWorkflowService,
    ) -> None:
        super().__init__(parent)
        self._session = session
        self._overlay = overlay
        self._pbs_ids = pbs_ids
        self._anchor = anchor
        self._location_group = location_group
        self._workflow = workflow
        self._scope_kind: BundleScopeKind = (
            "location_row" if location_group is not None else "pbs_selection"
        )
        self._preview: MeekoppelLocationPreview | None = None
        self._selection: MeekoppelPreviewSelectionModel | None = None
        self._checked_pm_ids: frozenset[str] = frozenset()
        self._syncing_checks = False

        self.setWindowTitle(messages.WORKSPACE_MEEKOPPEL_PREVIEW_DIALOG_TITLE)
        layout = QVBoxLayout(self)

        self._scope_label = QLabel("")
        self._scope_label.setWordWrap(True)
        layout.addWidget(self._scope_label)

        scope_row = QHBoxLayout()
        self._scope_row_button = QPushButton(messages.WORKSPACE_MEEKOPPEL_PREVIEW_SCOPE_ROW)
        self._scope_pbs_button = QPushButton(messages.WORKSPACE_MEEKOPPEL_PREVIEW_SCOPE_PBS)
        self._scope_row_button.clicked.connect(lambda: self._switch_scope("location_row"))
        self._scope_pbs_button.clicked.connect(lambda: self._switch_scope("pbs_selection"))
        scope_row.addWidget(self._scope_row_button)
        scope_row.addWidget(self._scope_pbs_button)
        scope_row.addStretch(1)
        layout.addLayout(scope_row)

        self._determined_label = QLabel("")
        self._determined_label.setWordWrap(True)
        layout.addWidget(self._determined_label)

        self._selection_summary_label = QLabel("")
        self._selection_summary_label.setWordWrap(True)
        layout.addWidget(self._selection_summary_label)

        filter_row = QHBoxLayout()
        self._filter_field = QLineEdit()
        self._filter_field.setPlaceholderText(
            messages.WORKSPACE_MEEKOPPEL_PREVIEW_FILTER_PLACEHOLDER
        )
        self._filter_field.textChanged.connect(self._on_row_filter_changed)
        self._filter_shift_button = QPushButton(
            messages.WORKSPACE_MEEKOPPEL_PREVIEW_FILTER_SHIFTING
        )
        self._filter_shift_button.setCheckable(True)
        self._filter_shift_button.toggled.connect(self._on_shifting_filter_toggled)
        filter_row.addWidget(self._filter_field, stretch=1)
        filter_row.addWidget(self._filter_shift_button)
        layout.addLayout(filter_row)

        bulk_row = QHBoxLayout()
        select_all_btn = QPushButton(messages.WORKSPACE_MEEKOPPEL_PREVIEW_SELECT_ALL_VISIBLE)
        select_all_btn.clicked.connect(self._on_select_all_visible)
        deselect_all_btn = QPushButton(
            messages.WORKSPACE_MEEKOPPEL_PREVIEW_DESELECT_ALL_VISIBLE
        )
        deselect_all_btn.clicked.connect(self._on_deselect_all_visible)
        bulk_row.addWidget(select_all_btn)
        bulk_row.addWidget(deselect_all_btn)
        bulk_row.addStretch(1)
        layout.addLayout(bulk_row)

        self._table = QTableWidget(0, 7, self)
        self._table.setHorizontalHeaderLabels(
            [
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_COL_SELECT,
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_COL_TASK,
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_COL_BASELINE,
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_COL_EFFECTIVE,
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_COL_TARGET,
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_COL_DELTA,
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_COL_STATUS,
            ]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table, stretch=1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Cancel
        )
        self._apply_button = buttons.button(QDialogButtonBox.StandardButton.Apply)
        self._apply_button.setText(messages.WORKSPACE_MEEKOPPEL_APPLY)
        self._apply_button.clicked.connect(self._on_apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._dialog_accepted_apply = False

        self._scope_row_button.setEnabled(location_group is not None)
        self._load_preview(notify_scope_switch=False)

    def result_payload(self) -> MeekoppelPreviewDialogResult:
        return MeekoppelPreviewDialogResult(
            accepted=self._dialog_accepted_apply,
            preview=self._preview,
            scope_kind=self._scope_kind,
            checked_pm_ids=self._checked_pm_ids,
        )

    def _switch_scope(self, kind: BundleScopeKind) -> None:
        if kind == self._scope_kind:
            return
        self._scope_kind = kind
        self._load_preview(notify_scope_switch=True)

    def _load_preview(self, *, notify_scope_switch: bool) -> None:
        wf = self._workflow.preview(
            session=self._session,
            overlay=self._overlay,
            pbs_ids=self._pbs_ids,
            anchor=self._anchor,
            scope_kind=self._scope_kind,
            location_group=self._location_group
            if self._scope_kind == "location_row"
            else None,
        )
        if wf.status != "ok" or wf.preview_payload is None:
            QMessageBox.warning(
                self,
                messages.LTAP_ERROR_DIALOG_TITLE,
                wf.user_message or messages.WORKSPACE_MEEKOPPEL_PREVIEW_BLOCKED.format(
                    reason=messages.WORKSPACE_MEEKOPPEL_SELECT_MIN_REV
                ),
            )
            self.reject()
            return
        self._preview = wf.preview_payload
        insight = self._preview.bundle_insight
        if insight is not None:
            self._scope_label.setText(insight.summary_lines[0])
            self._determined_label.setText(insight.summary_lines[1])
            self._selection = MeekoppelPreviewSelectionModel.from_task_rows(
                insight.task_rows,
                anchor=self._anchor,
            )
            self._refresh_table()
        else:
            self._scope_label.setText(self._preview.path_label)
            self._determined_label.setText("")
            self._selection = None
            self._populate_legacy()
        if notify_scope_switch:
            self._filter_field.blockSignals(True)
            self._filter_field.clear()
            self._filter_field.blockSignals(False)
            self._filter_shift_button.blockSignals(True)
            self._filter_shift_button.setChecked(False)
            self._filter_shift_button.setText(
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_FILTER_SHIFTING
            )
            self._filter_shift_button.blockSignals(False)
            QMessageBox.information(
                self,
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_DIALOG_TITLE,
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_SCOPE_SWITCH_NOTICE,
            )
        self._update_apply_enabled()

    def _refresh_table(self) -> None:
        if self._selection is None:
            return
        self._syncing_checks = True
        try:
            self._populate_table(self._selection.visible_rows())
            self._selection_summary_label.setText(self._selection.summary_line())
            self._determined_label.setText(self._selection.determined_by_line())
        finally:
            self._syncing_checks = False
        self._update_apply_enabled()

    def _populate_table(self, rows) -> None:
        self._table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            cb = QCheckBox()
            shiftable = is_shiftable(row)
            cb.setEnabled(shiftable)
            cb.setChecked(self._selection is not None and self._selection.is_checked(row.pm_id))
            cb.stateChanged.connect(
                lambda _state, pm_id=row.pm_id: self._on_row_check_changed(pm_id)
            )
            self._table.setCellWidget(i, 0, cb)
            self._set_item(i, 1, row.task_label, row.is_target_driver)
            self._set_item(i, 2, str(row.baseline_year), False)
            self._set_item(i, 3, str(row.effective_year), False)
            self._set_item(i, 4, str(row.target_year), False)
            self._set_item(i, 5, str(row.delta_years), False)
            status = row.blocked_reason or (
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_NO_MOVES
                if row.delta_years == 0
                else ""
            )
            self._set_item(i, 6, status, False)

    def _populate_legacy(self) -> None:
        assert self._preview is not None
        self._table.setRowCount(0)
        self._selection_summary_label.setText("")

    def _set_item(self, row: int, col: int, text: str, highlight: bool = False) -> None:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if highlight:
            item.setBackground(Qt.GlobalColor.lightGray)
        self._table.setItem(row, col, item)

    def _on_row_check_changed(self, pm_id: str) -> None:
        if self._syncing_checks or self._selection is None:
            return
        widget = self.sender()
        if not isinstance(widget, QCheckBox):
            return
        self._selection = self._selection.set_checked(pm_id, widget.isChecked())
        self._selection_summary_label.setText(self._selection.summary_line())
        self._determined_label.setText(self._selection.determined_by_line())
        self._refresh_table()

    def _on_row_filter_changed(self, text: str) -> None:
        if self._selection is None:
            return
        self._selection = self._selection.with_row_filter(text)
        self._refresh_table()

    def _on_shifting_filter_toggled(self, checked: bool) -> None:
        if self._selection is None:
            return
        self._selection = self._selection.with_visibility_filter(
            "shifting_only" if checked else "all"
        )
        self._filter_shift_button.setText(
            messages.WORKSPACE_MEEKOPPEL_PREVIEW_FILTER_ALL
            if checked
            else messages.WORKSPACE_MEEKOPPEL_PREVIEW_FILTER_SHIFTING
        )
        self._refresh_table()

    def _on_select_all_visible(self) -> None:
        if self._selection is None:
            return
        self._selection = self._selection.bulk_select_visible()
        self._refresh_table()

    def _on_deselect_all_visible(self) -> None:
        if self._selection is None:
            return
        self._selection = self._selection.bulk_deselect_visible()
        self._refresh_table()

    def _update_apply_enabled(self) -> None:
        if self._selection is None:
            self._apply_button.setEnabled(False)
            return
        self._apply_button.setEnabled(self._selection.apply_enabled())

    def _on_apply(self) -> None:
        if self._selection is None:
            return
        selected = self._selection.apply_eligible_pm_ids()
        if len(selected) < 2:
            return
        assert self._preview is not None
        insight = self._preview.bundle_insight
        scope_label = insight.scope_label if insight else self._preview.path_label
        modeljaar = int(self._session.loaded.core().config.modeljaar)
        confirm = QMessageBox.question(
            self,
            messages.WORKSPACE_MEEKOPPEL_PREVIEW_DIALOG_TITLE,
            messages.WORKSPACE_MEEKOPPEL_PREVIEW_APPLY_CONFIRM.format(
                scope_label=scope_label,
                count=len(selected),
                target=self._selection.target_year(),
                target_cal=due_calendar_year(
                    modeljaar, self._selection.target_year()
                ),
            ),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._checked_pm_ids = selected
        self._dialog_accepted_apply = True
        self.accept()
