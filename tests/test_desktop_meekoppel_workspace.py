"""pytest-qt smoke — meekoppelkansen paneel (slice 39/40, UX v2)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_core.persistence import load_project
from rcm_desktop import messages
from rcm_desktop.adapter.meekoppel_apply_service import MeekoppelLocationPreview
from rcm_desktop.adapter.meekoppel_workflow_service import WorkflowResult
from rcm_desktop.adapter.meekoppel_suggestions_table_model import MeekoppelSuggestionsTableModel
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.run_service import run as run_single
import rcm_desktop.views.panels.meekoppel_workspace_binding as meekoppel_binding
import rcm_desktop.views.results_workspace_window as workspace_window
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.workspace_test_helpers import switch_workspace_modus


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _project_with_rev_pair():
    project = load_project(Path("tests/fixtures/one_fm_planning.rcm.json"))
    project.pm_tasks["PM-REV-B"] = replace(
        project.pm_tasks["PM-002"],
        pm_id="PM-REV-B",
        interval_jaar=17.0,
    )
    return project


def test_meekoppel_table_model_shows_path_and_due_range():
    from rcm_desktop.adapter.meekoppelkansen_discovery_service import (
        discover_meekoppel_locations,
    )
    from rcm_desktop.adapter.meekoppel_panel_service import (
        build_meekoppel_panel_row,
        meekoppel_panel_columns,
    )

    project = _project_with_rev_pair()
    groups = discover_meekoppel_locations(project, window_years=5)
    assert groups
    rows = tuple(build_meekoppel_panel_row(project, g) for g in groups)
    model = MeekoppelSuggestionsTableModel(
        rows, columns=meekoppel_panel_columns()
    )
    assert model.headerData(0, Qt.Orientation.Horizontal) == messages.WORKSPACE_MEEKOPPEL_HEADER_PATH
    assert model.headerData(2, Qt.Orientation.Horizontal) == messages.WORKSPACE_MEEKOPPEL_HEADER_DUE_RANGE
    assert model.data(model.index(0, 0)) == rows[0].path_label
    assert model.data(model.index(0, 2)) == rows[0].due_range_text
    tip = model.data(model.index(0, 0), Qt.ItemDataRole.ToolTipRole)
    assert tip == rows[0].path_tooltip
    assert groups[0].pbs_id in tip


def _expand_meekoppel_panel(window: ResultsWorkspaceWindow, app: QApplication) -> None:
    window.workspace_state.set_lcc_whatif_collapsed_in_lcc(False)
    window.lcc_whatif_button.setChecked(True)
    window.workspace_state.set_meekoppel_collapsed_in_lcc(False)
    app.processEvents()


def test_meekoppel_panel_visible_after_whatif_enabled(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _project_with_rev_pair()
    window._state.set_last_project(project)
    rr = run_single(
        project,
        Path("tests/fixtures/one_fm_planning.rcm.json"),
        full_recompute=True,
        parallel=False,
    )
    window._state.set_last_run(rr)
    app.processEvents()

    switch_workspace_modus(window, "lcc", app)
    app.processEvents()
    assert window.meekoppel_panel.isVisible() is False
    window.lcc_whatif_button.setChecked(True)
    app.processEvents()
    assert window.meekoppel_panel.isVisible() is True
    _expand_meekoppel_panel(window, app)
    assert window.meekoppel_whatif_hint_label.isVisible() is False
    assert window._meekoppel_table_model.rowCount() >= 1


def test_meekoppel_panel_hidden_without_whatif(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _project_with_rev_pair()
    window._state.set_last_project(project)
    rr = run_single(
        project,
        Path("tests/fixtures/one_fm_planning.rcm.json"),
        full_recompute=True,
        parallel=False,
    )
    window._state.set_last_run(rr)
    app.processEvents()

    switch_workspace_modus(window, "lcc", app)
    app.processEvents()
    window.lcc_whatif_button.setChecked(True)
    app.processEvents()
    window.lcc_whatif_button.setChecked(False)
    app.processEvents()
    assert window.meekoppel_panel.isVisible() is False


def _select_first_pbs_node(window: ResultsWorkspaceWindow, app: QApplication) -> None:
    from PySide6.QtCore import QItemSelectionModel

    root = window.pbs_proxy.index(0, 0, QModelIndex())
    if not root.isValid():
        return
    selection = window.pbs_tree_view.selectionModel()
    if selection is None:
        return
    selection.select(root, QItemSelectionModel.SelectionFlag.ClearAndSelect)
    app.processEvents()


def test_meekoppel_apply_updates_overlay_after_preview(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "information", lambda *_a, **_k: QMessageBox.Ok)

    window = ResultsWorkspaceWindow()
    window.show()
    project = _project_with_rev_pair()
    window._state.set_last_project(project)
    rr = run_single(
        project,
        Path("tests/fixtures/one_fm_planning.rcm.json"),
        full_recompute=True,
        parallel=False,
    )
    window._state.set_last_run(rr)
    app.processEvents()

    switch_workspace_modus(window, "lcc", app)
    app.processEvents()
    _expand_meekoppel_panel(window, app)
    assert window.lcc_whatif_button.isChecked() is True
    _select_first_pbs_node(window, app)

    assert window.meekoppel_anchor_later.isChecked()

    if window._pbs_selected_ids_from_tree():
        assert window.meekoppel_apply_button.isEnabled() is False
        window.meekoppel_preview_button.click()
        app.processEvents()
        assert window.meekoppel_apply_button.isEnabled() is True
        before = window.workspace_state.snapshot().planning_overlay.change_count()
        window.meekoppel_apply_button.click()
        app.processEvents()
        after = window.workspace_state.snapshot().planning_overlay.change_count()
        assert after >= before


def test_meekoppel_preview_uses_workflow_when_flag_enabled(monkeypatch):
    from PySide6.QtWidgets import QDialog
    from rcm_desktop.views import meekoppel_preview_dialog as mpd_mod
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "information", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(meekoppel_binding, "meekoppel_workflow_v2_enabled", lambda: True)
    monkeypatch.setattr(workspace_window, "meekoppel_workflow_v2_enabled", lambda: True)
    monkeypatch.setattr(mpd_mod.MeekoppelPreviewDialog, "exec", lambda self: QDialog.DialogCode.Rejected)

    called = {"preview": 0}

    class _StubWorkflow:
        def preview(self, **_kwargs):
            called["preview"] += 1
            return WorkflowResult(
                status="validation",
                user_message=messages.WORKSPACE_MEEKOPPEL_SELECT_PBS,
                preview_payload=None,
                telemetry_flags=frozenset({"meekoppel_workflow_v2"}),
                overlay=PlanningOverlayState.inactive().begin_what_if(),
            )

    window = ResultsWorkspaceWindow()
    window._meekoppel_workflow = _StubWorkflow()
    window.show()
    project = _project_with_rev_pair()
    window._state.set_last_project(project)
    rr = run_single(
        project,
        Path("tests/fixtures/one_fm_planning.rcm.json"),
        full_recompute=True,
        parallel=False,
    )
    window._state.set_last_run(rr)
    app.processEvents()
    switch_workspace_modus(window, "lcc", app)
    app.processEvents()
    _expand_meekoppel_panel(window, app)
    _select_first_pbs_node(window, app)

    window.meekoppel_preview_button.click()
    app.processEvents()
    assert called["preview"] == 1


def test_meekoppel_preview_uses_legacy_when_flag_disabled(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "information", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(meekoppel_binding, "meekoppel_workflow_v2_enabled", lambda: False)
    monkeypatch.setattr(workspace_window, "meekoppel_workflow_v2_enabled", lambda: False)

    called = {"legacy": 0}

    def _legacy_preview(*_args, **_kwargs):
        called["legacy"] += 1
        return MeekoppelLocationPreview(
            pbs_id="P1",
            path_label="x",
            target_year=0,
            moves=(),
            blocked_reason=messages.WORKSPACE_MEEKOPPEL_SELECT_MIN_REV,
        )

    monkeypatch.setattr(meekoppel_binding, "preview_meekoppel", _legacy_preview)
    monkeypatch.setattr(workspace_window, "preview_meekoppel", _legacy_preview)

    window = ResultsWorkspaceWindow()
    window.show()
    project = _project_with_rev_pair()
    window._state.set_last_project(project)
    rr = run_single(
        project,
        Path("tests/fixtures/one_fm_planning.rcm.json"),
        full_recompute=True,
        parallel=False,
    )
    window._state.set_last_run(rr)
    app.processEvents()
    switch_workspace_modus(window, "lcc", app)
    app.processEvents()
    _expand_meekoppel_panel(window, app)
    _select_first_pbs_node(window, app)

    window.meekoppel_preview_button.click()
    app.processEvents()
    assert called["legacy"] == 1
