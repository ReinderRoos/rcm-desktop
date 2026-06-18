"""Slice 87 — Input entiteiten-grid: PBS-scope, zoekbalk en performance."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.persistence import load_project

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_desktop import messages
from rcm_desktop.adapter.entity_edit_service import EntityEditService
from rcm_desktop.adapter.entity_grid_config import entity_grid_config_for_view
from rcm_desktop.adapter.input_scope_policy import (
    InputScopeMode,
    input_scope_mode,
    row_in_scope,
    row_pbs_id,
)
from rcm_desktop.adapter.input_search_text import build_row_search_haystack
from rcm_desktop.adapter.result_filter_service import collect_pbs_subtree_ids
from rcm_desktop.views.input_entity_filter_proxy import InputEntityFilterProxy
from rcm_desktop.views.panels.entity_grid_panel import EntityGridPanel
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from rcm_desktop.views.widgets.table_filter_row import TableFilterRowWidget

from tests.test_desktop_results_workspace_window import _ensure_app


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def test_faalwijzen_input_scope_mode_is_pbs_bound() -> None:
    assert input_scope_mode("input.faalwijzen") == InputScopeMode.PBS_BOUND


def test_effecten_input_scope_mode_is_project_wide() -> None:
    assert input_scope_mode("input.effecten") == InputScopeMode.PROJECT_WIDE


def test_row_pbs_id_for_faalwijzen(sample_project) -> None:
    fw = sample_project.faalwijzes["FM-001"]
    assert row_pbs_id("input.faalwijzen", {"pbs_id": fw.pbs_id}, sample_project) == "PBS-001-1"


def test_row_pbs_id_for_rev_tasks_via_fm(sample_project) -> None:
    pm = next(pm for pm in sample_project.pm_tasks.values() if pm.fm_id == "FM-004")
    assert row_pbs_id("input.rev_tasks", {"fm_id": pm.fm_id}, sample_project) == "PBS-001-2"


def test_row_in_scope_none_shows_all_faalwijzen(sample_project) -> None:
    for fw in sample_project.faalwijzes.values():
        assert row_in_scope(
            "input.faalwijzen",
            {"pbs_id": fw.pbs_id},
            sample_project,
            None,
        )


def test_row_in_scope_subtree_filters_faalwijzen(sample_project) -> None:
    subtree = collect_pbs_subtree_ids(sample_project, "PBS-001-2")
    in_scope = [
        fw
        for fw in sample_project.faalwijzes.values()
        if row_in_scope("input.faalwijzen", {"pbs_id": fw.pbs_id}, sample_project, "PBS-001-2")
    ]
    assert len(in_scope) == sum(1 for fw in sample_project.faalwijzes.values() if fw.pbs_id in subtree)


def test_row_in_scope_unknown_scope_excludes_rows(sample_project) -> None:
    assert (
        row_in_scope(
            "input.faalwijzen",
            {"pbs_id": "PBS-001-1"},
            sample_project,
            "PBS-UNKNOWN",
        )
        is False
    )


def test_search_haystack_includes_key_field_and_failure_type_label(sample_project) -> None:
    cfg = entity_grid_config_for_view("input.faalwijzen")
    assert cfg is not None
    fw = sample_project.faalwijzes["FM-001"]
    hay = build_row_search_haystack(
        cfg,
        sample_project,
        fw.to_dict(),
        cfg.preset_columns,
    )
    assert "fm-001" in hay
    assert messages.FAALWIJZEN_FAILURE_AGING.lower() in hay
    assert "aging" in hay


def test_entity_edit_rows_cache_discard_restores(sample_project) -> None:
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    before = svc.rows()
    svc.apply_change("FM-001", "mttf_jaar", "99")
    svc.discard_changes()
    assert svc.rows() == before


def test_correctief_scope_uses_pbs_id(sample_project) -> None:
    _ensure_app()
    svc = EntityEditService.for_view("input.correctief")
    svc.init(sample_project)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.correctief")
    panel.set_scope("PBS-001-2", sample_project)
    assert panel.visible_row_count() < panel.row_count()


def test_entity_edit_rows_cache_reflects_mutation(sample_project) -> None:
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    first = svc.rows()
    second = svc.rows()
    assert first == second
    svc.apply_change("FM-001", "mttf_jaar", "42")
    updated = svc.rows()
    assert updated != first
    assert next(r for r in updated if r.row_key == "FM-001").values["mttf_jaar"] == pytest.approx(42.0)


def test_input_filter_proxy_scope_and_search(sample_project) -> None:
    _ensure_app()
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    cfg = entity_grid_config_for_view("input.faalwijzen")
    assert cfg is not None
    from rcm_desktop.adapter.entity_table_model import EntityTableModel

    model = EntityTableModel(svc, sample_project, cfg, cfg.preset_columns, hidden_columns=frozenset())
    proxy = InputEntityFilterProxy("input.faalwijzen")
    proxy.setSourceModel(model)
    proxy.set_scope("PBS-001-2", sample_project)
    assert proxy.rowCount() < model.rowCount()
    proxy.set_search_text("FM-004")
    assert proxy.rowCount() == 1


def test_entity_grid_search_reduces_visible_rows(sample_project) -> None:
    _ensure_app()
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.faalwijzen")
    assert panel.findChildren(TableFilterRowWidget) == []
    total = panel.row_count()
    panel.set_search_text("FM-001")
    assert panel.visible_row_count() == 1
    assert total == len(sample_project.faalwijzes)
    assert "1 van" in panel.row_count_label_text()


def test_entity_grid_scope_filters_faalwijzen(sample_project) -> None:
    _ensure_app()
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.faalwijzen")
    panel.set_search_text("FM-001")
    panel.set_scope("PBS-001-2", sample_project)
    assert panel.search_text() == "FM-001"
    assert panel.visible_row_count() == 0


def test_entity_grid_view_switch_clears_search(sample_project) -> None:
    _ensure_app()
    svc_fw = EntityEditService.for_view("input.faalwijzen")
    svc_fw.init(sample_project)
    svc_rev = EntityEditService.for_view("input.rev_tasks")
    svc_rev.init(sample_project)
    panel = EntityGridPanel()
    panel.attach(svc_fw, sample_project, view_id="input.faalwijzen")
    panel.set_search_text("FM-001")
    panel.attach(svc_rev, sample_project, view_id="input.rev_tasks")
    assert panel.search_text() == ""


def test_rev_tasks_scope_via_fm_id(sample_project) -> None:
    _ensure_app()
    svc = EntityEditService.for_view("input.rev_tasks")
    svc.init(sample_project)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.rev_tasks")
    panel.set_scope("PBS-001-2", sample_project)
    assert panel.visible_row_count() < panel.row_count()


def test_effecten_shows_scope_status_not_filter(sample_project) -> None:
    _ensure_app()
    svc = EntityEditService.for_view("input.effecten")
    svc.init(sample_project)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.effecten")
    total = panel.row_count()
    panel.set_scope("PBS-001-2", sample_project)
    assert panel.visible_row_count() == total
    assert panel.scope_status_visible()
    assert "effecten" in panel.scope_status_text().lower()


def test_workspace_scope_filters_faalwijzen_input(sample_project) -> None:
    app = _ensure_app()
    window = ResultsWorkspaceWindow()
    window.show()
    window._state.set_last_project(sample_project)
    window.workspace_state.set_workspace_side("input")
    window.workspace_state.set_active_view("input.faalwijzen")
    app.processEvents()
    total = window._entity_grid_panel.row_count()
    window.set_pbs_scope("PBS-001-2")
    app.processEvents()
    assert window._entity_grid_panel.visible_row_count() < total


def test_column_toggle_keeps_table_model(sample_project) -> None:
    _ensure_app()
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.faalwijzen")
    model_before = panel.table_model()
    panel.set_hidden_columns(frozenset({"fm_id"}))
    assert panel.table_model() is model_before


def test_search_finds_key_field_when_column_hidden(sample_project) -> None:
    _ensure_app()
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.faalwijzen")
    panel.set_hidden_columns(frozenset({"fm_id"}))
    panel.set_search_text("FM-001")
    assert panel.visible_row_count() == 1


def test_workspace_effecten_shows_scope_status(sample_project) -> None:
    app = _ensure_app()
    window = ResultsWorkspaceWindow()
    window.show()
    window._state.set_last_project(sample_project)
    window.workspace_state.set_workspace_side("input")
    window.workspace_state.set_active_view("input.effecten")
    app.processEvents()
    window.set_pbs_scope("PBS-001-2")
    app.processEvents()
    assert window._entity_grid_panel.scope_status_visible()
