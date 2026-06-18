"""Chrome-footer binding (slice 107, ADR-0020)."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QVBoxLayout, QWidget

from rcm_desktop.adapter.results_workspace_orchestrator import WorkspaceChromeFooterPlan
from rcm_desktop.adapter.workspace_view_registry import WORKSPACE_CHROME_FOOTER_RIGHT_WIDTH_PX
from rcm_desktop.views.panels.workspace_toolbar_sync import (
    apply_top10_subbar_visibility,
    relocate_fm_metric_chrome,
)


def build_chrome_footer_zones(window: Any) -> None:
    """Reserveer drie zones in WorkspaceChromeFooter."""
    footer = window.chrome_footer
    layout = footer.layout()
    if layout is None:
        return
    while layout.count() > 1:
        item = layout.takeAt(1)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()

    window.chrome_footer_middle = QWidget(footer)
    window.chrome_footer_middle.setObjectName("WorkspaceChromeFooterMiddle")
    middle_layout = window.chrome_footer_middle.layout()
    if middle_layout is None:
        from PySide6.QtWidgets import QHBoxLayout

        middle_layout = QHBoxLayout(window.chrome_footer_middle)
        middle_layout.setContentsMargins(0, 0, 0, 0)
    window._chrome_footer_middle_layout = middle_layout

    window.chrome_footer_right = QWidget(footer)
    window.chrome_footer_right.setObjectName("WorkspaceChromeFooterRight")
    window.chrome_footer_right.setFixedWidth(WORKSPACE_CHROME_FOOTER_RIGHT_WIDTH_PX)
    right_layout = window.chrome_footer_right.layout()
    if right_layout is None:
        right_layout = QVBoxLayout(window.chrome_footer_right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(2)
    window._chrome_footer_right_layout = right_layout

    layout.addWidget(window.chrome_footer_middle, stretch=1)
    layout.addWidget(window.chrome_footer_right)


def apply_chrome_footer_plan(window: Any, plan: WorkspaceChromeFooterPlan) -> None:
    window.chrome_footer.setVisible(plan.visible)
    window.chrome_footer_context_label.setText("")
    window.chrome_footer_context_label.setVisible(False)

    lcc_footer_middle = plan.lcc_toolbar is not None and plan.middle_chrome_visible
    fm_metric_on_detail_toolbar = (
        plan.fm_toolbar is not None and plan.fm_toolbar.metric_combo_visible
    )

    if lcc_footer_middle:
        apply_top10_subbar_visibility(window, True)
        _mount_top10_in_footer_middle(window)
        relocate_fm_metric_chrome(window, target="top10")
    else:
        apply_top10_subbar_visibility(window, False)
        if fm_metric_on_detail_toolbar:
            relocate_fm_metric_chrome(window, target="fm")
            if hasattr(window, "fm_metric_chrome_host"):
                window.fm_metric_chrome_host.setVisible(True)
        elif hasattr(window, "fm_metric_chrome_host"):
            window.fm_metric_chrome_host.setVisible(False)

    window.chrome_footer_right.setVisible(True)
    _apply_lcc_measure_stack(window, plan)


def _mount_top10_in_footer_middle(window: Any) -> None:
    if not hasattr(window, "_chrome_footer_middle_layout"):
        return
    bar = getattr(window, "top10_subbar", None)
    if bar is None:
        return
    bar.setParent(window.chrome_footer_middle)
    layout = window._chrome_footer_middle_layout
    if layout.indexOf(bar) < 0:
        layout.addWidget(bar)


def _apply_lcc_measure_stack(window: Any, plan: WorkspaceChromeFooterPlan) -> None:
    layout = getattr(window, "_chrome_footer_right_layout", None)
    checks = getattr(window, "_lcc_filter_checks", None)
    if layout is None or checks is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
    if not plan.lcc_measure_stack_visible:
        return
    for key in ("cm", "rev", "in_task", "tst", "svo", "wet"):
        box = checks.get(key)
        if box is not None:
            layout.addWidget(box)
    layout.addStretch(1)
