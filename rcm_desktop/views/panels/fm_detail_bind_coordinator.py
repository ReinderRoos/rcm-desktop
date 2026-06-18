"""FM-detail bind coordinator — slice 106 issue 03."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QWidget

from rcm_desktop.adapter.column_fit_policy import ColumnFitMode
from rcm_desktop.adapter.faalwijze_analyse_service import (
    FM_COMPARE_VIEW_DIAGRAM,
    FM_COMPARE_VIEW_TABLE,
)
from rcm_desktop.adapter.results_workspace_orchestrator import FmToolbarPlan, RenderPlan
from rcm_desktop.adapter.results_workspace_state import WorkspaceStateSnapshot
from rcm_desktop.views.panels import fm_detail_workspace_binding as binding
from rcm_desktop.views.panels.workspace_toolbar_sync import apply_fm_toolbar


class FmDetailBindCoordinator:
    """Apply FM toolbar + render plans; owns FM view-mode chrome wiring."""

    def __init__(self, window: Any) -> None:
        self._window = window

    @property
    def view_mode(self) -> str:
        return self._window.workspace_state.snapshot().fm_view_mode

    def set_view_mode(self, mode: str) -> None:
        binding.set_fm_view_mode(self._window, mode)

    def sync_view_mode_buttons(self, mode: str) -> None:
        binding.sync_fm_view_mode_buttons(self._window, mode)

    def sync_compare_view_chrome(self, *, show_nmf_rf: bool) -> None:
        binding.sync_fm_compare_view_chrome(self._window, show_nmf_rf=show_nmf_rf)

    def sync_single_view_chrome(self, *, show_nmf_rf: bool) -> None:
        binding.sync_fm_single_view_chrome(self._window, show_nmf_rf=show_nmf_rf)

    def sync_nmf_rf_toggles(self, checked: bool) -> None:
        for toggle in (
            getattr(self._window, "fm_compare_nmf_rf_toggle", None),
            getattr(self._window, "fm_single_nmf_rf_toggle", None),
        ):
            if toggle is None or toggle.isChecked() == checked:
                continue
            blocker = toggle.blockSignals(True)
            toggle.setChecked(checked)
            toggle.blockSignals(blocker)

    def layout_compare_chart(self) -> None:
        binding.layout_fm_compare_chart(self._window)

    def layout_single_chart(self) -> None:
        binding.layout_fm_single_chart(self._window)

    def apply_toolbar(self, toolbar: FmToolbarPlan | None) -> None:
        if toolbar is None:
            return
        self._window._last_fm_toolbar_plan = toolbar
        lcc_plan = getattr(self._window, "_last_lcc_toolbar_plan", None)
        preserve = (
            lcc_plan is not None
            and lcc_plan.metric_combo_visible
            and not toolbar.metric_combo_visible
        )
        apply_fm_toolbar(self._window, toolbar, preserve_shared_metric=preserve)

    def apply_render(self, plan: RenderPlan, snapshot: WorkspaceStateSnapshot) -> None:
        if plan.kind == "fm":
            binding.apply_fm_detail_render(self._window, plan, snapshot)
        elif plan.kind == "fm_compare":
            binding.apply_fm_compare_render(self._window, plan, snapshot)

    def apply_column_fit_mode(self, mode: ColumnFitMode) -> None:
        binding.apply_fm_column_fit_mode(self._window, mode)

    def apply_optional_column_visibility(self) -> None:
        binding.apply_fm_optional_column_visibility(self._window)

    def wire_panel(self, panel: Any) -> None:
        panel.fm_compare_nmf_rf_toggle.toggled.connect(self.on_compare_nmf_rf_toggled)
        panel.fm_compare_table_view_button.toggled.connect(
            self.on_compare_table_view_toggled
        )
        panel.fm_compare_diagram_view_button.toggled.connect(
            self.on_compare_diagram_view_toggled
        )
        panel.fm_single_nmf_rf_toggle.toggled.connect(self.on_single_nmf_rf_toggled)
        panel.fm_single_table_view_button.toggled.connect(
            self.on_single_table_view_toggled
        )
        panel.fm_single_diagram_view_button.toggled.connect(
            self.on_single_diagram_view_toggled
        )

    def on_compare_table_view_toggled(self, checked: bool) -> None:
        if checked:
            self.set_view_mode(FM_COMPARE_VIEW_TABLE)

    def on_compare_diagram_view_toggled(self, checked: bool) -> None:
        if checked:
            self.set_view_mode(FM_COMPARE_VIEW_DIAGRAM)

    def on_single_table_view_toggled(self, checked: bool) -> None:
        if checked:
            self.set_view_mode(FM_COMPARE_VIEW_TABLE)

    def on_single_diagram_view_toggled(self, checked: bool) -> None:
        if checked:
            self.set_view_mode(FM_COMPARE_VIEW_DIAGRAM)

    def on_compare_nmf_rf_toggled(self, checked: bool) -> None:
        self._on_nmf_rf_toggled(checked)

    def on_single_nmf_rf_toggled(self, checked: bool) -> None:
        self._on_nmf_rf_toggled(checked)

    def _on_nmf_rf_toggled(self, checked: bool) -> None:
        self._window.workspace_state.set_fm_show_nmf_rf(checked)
        self.sync_nmf_rf_toggles(checked)
        self._window._rerender_detail_for_current_scope()

    def handle_chart_viewport_resize(self, watched: QWidget, event: QEvent) -> bool:
        if (
            watched is self._window.fm_compare_chart_scroll.viewport()
            and event.type() == QEvent.Type.Resize
            and self.view_mode == FM_COMPARE_VIEW_DIAGRAM
        ):
            self.layout_compare_chart()
            return True
        if (
            hasattr(self._window, "fm_single_chart_scroll")
            and watched is self._window.fm_single_chart_scroll.viewport()
            and event.type() == QEvent.Type.Resize
            and self.view_mode == FM_COMPARE_VIEW_DIAGRAM
        ):
            self.layout_single_chart()
            return True
        return False
