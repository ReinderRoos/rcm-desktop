"""Slice 83 — generiek entiteiten-grid (tracer: Faalwijzen)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.editing.schemas import ENTITY_SCHEMAS
from rcm_core.persistence import load_project

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from rcm_desktop.adapter.entity_edit_service import EntityEditService
from rcm_desktop.adapter.entity_grid_config import (
    ENTITY_GRID_VIEW_CONFIGS,
    entity_grid_config_for_view,
    schema_columns_for_view,
    validate_entity_grid_configs,
)
from rcm_desktop.adapter.results_workspace_orchestrator import ResultsWorkspaceOrchestrator
from rcm_desktop.adapter.results_workspace_state import (
    ResultsWorkspaceState,
    WorkspaceStateSnapshot,
)
from rcm_desktop.views.panels.entity_grid_panel import EntityGridPanel
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import _ensure_app


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


@pytest.mark.parametrize(
    "view_id,entity",
    [
        ("input.faalwijzen", "faalwijzes"),
        ("input.rev_tasks", "pm_tasks"),
        ("input.effecten", "effect_klassen"),
        ("input.taakgroepen", "task_groups"),
        ("input.correctief", "faalwijzes"),
    ],
)
def test_all_input_view_presets_exist_in_schema(view_id, entity) -> None:
    validate_entity_grid_configs(ENTITY_GRID_VIEW_CONFIGS)
    cfg = entity_grid_config_for_view(view_id)
    assert cfg is not None
    assert cfg.entity == entity
    schema_fields = set(ENTITY_SCHEMAS[entity]["field_types"])
    for col in cfg.preset_columns:
        if col in cfg.derived_columns:
            continue
        assert col in schema_fields


def test_faalwijzen_preset_columns_exist_in_schema() -> None:
    test_all_input_view_presets_exist_in_schema("input.faalwijzen", "faalwijzes")


@pytest.mark.parametrize("view_id", ["input.rev_tasks", "input.effecten", "input.taakgroepen"])
def test_entity_edit_apply_change_on_parametrized_views(sample_project, view_id) -> None:
    svc = EntityEditService.for_view(view_id)
    svc.init(sample_project)
    rows = svc.rows()
    assert rows
    row = rows[0]
    editable = next(f for f in row.editable_fields if f != svc.config.key_field)
    before = row.values.get(editable)
    svc.apply_change(row.row_key, editable, before)
    assert svc.error_count() == 0


def test_correctief_projection_edits_underlying_faalwijze(sample_project) -> None:
    cm = EntityEditService.for_view("input.correctief")
    fw = EntityEditService.for_view("input.faalwijzen")
    cm.init(sample_project)
    fw.attach_editing_session(cm.editing_session)
    cm.apply_change("FM-001", "cost_cm_eur", "999")
    fw_row = next(r for r in fw.rows() if r.row_key == "FM-001")
    assert fw_row.values["cost_cm_eur"] == pytest.approx(999.0)


def test_correctief_and_faalwijzen_share_dirty_session(sample_project) -> None:
    cm = EntityEditService.for_view("input.correctief")
    fw = EntityEditService.for_view("input.faalwijzen")
    cm.init(sample_project)
    fw.attach_editing_session(cm.editing_session)
    cm.apply_change("FM-001", "cost_cm_eur", "888")
    fw_row = next(r for r in fw.rows() if r.row_key == "FM-001")
    assert fw_row.values["cost_cm_eur"] == pytest.approx(888.0)


def test_hidden_columns_fall_back_for_unknown_settings_keys() -> None:
    from rcm_desktop.adapter.entity_grid_column_settings import (
        default_hidden_columns,
        read_hidden_entity_columns,
    )

    class _Settings:
        def __init__(self, raw: str) -> None:
            self._raw = raw

        def value(self, key: str, default=None, type=None):
            if key.endswith("hidden_columns"):
                return self._raw
            return default

        def setValue(self, key: str, value) -> None:
            pass

    hidden = read_hidden_entity_columns(
        _Settings("bogus_col,notes,cost_cm_eur"),
        "input.faalwijzen",
    )
    assert "bogus_col" not in hidden
    assert hidden == frozenset({"notes", "cost_cm_eur"})


def test_resolve_visible_columns_shows_optional_when_unhidden() -> None:
    from rcm_desktop.adapter.entity_grid_column_settings import resolve_visible_columns

    visible = resolve_visible_columns("input.faalwijzen", frozenset())
    assert "fm_id" in visible
    assert "notes" in visible


def test_workspace_column_choice_persists_per_view(sample_project, tmp_path, monkeypatch) -> None:
    from PySide6.QtCore import QSettings

    app = _ensure_app()
    settings_path = tmp_path / "settings.ini"
    monkeypatch.setenv("QT_SETTINGS_INI", str(settings_path))
    settings = QSettings(str(settings_path), QSettings.Format.IniFormat)

    from rcm_desktop.adapter.entity_grid_column_settings import (
        read_hidden_entity_columns,
        write_hidden_entity_columns,
    )

    write_hidden_entity_columns(settings, "input.faalwijzen", frozenset({"fm_id"}))
    assert "fm_id" in read_hidden_entity_columns(settings, "input.faalwijzen")
    write_hidden_entity_columns(settings, "input.rev_tasks", frozenset({"pm_id"}))
    assert "fm_id" in read_hidden_entity_columns(settings, "input.faalwijzen")
    assert "pm_id" in read_hidden_entity_columns(settings, "input.rev_tasks")


def test_entity_edit_apply_change_on_faalwijzen_view(sample_project) -> None:
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "20")
    row = next(r for r in svc.rows() if r.row_key == "FM-001")
    assert row.values["mttf_jaar"] == 20.0
    assert not svc.has_errors()


def test_entity_edit_marks_dirty_via_edit_dirty_global(sample_project) -> None:
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    session = svc.editing_session.session
    assert session.get("edit_dirty_global") is False
    svc.apply_change("FM-001", "mttf_jaar", "21")
    assert session.get("edit_dirty_global") is True


def _snap(**kwargs) -> WorkspaceStateSnapshot:
    base = ResultsWorkspaceState().snapshot()
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    data.update(kwargs)
    return WorkspaceStateSnapshot(**data)


def test_faalwijzen_view_orchestrator_shows_entity_grid_not_placeholder() -> None:
    snap = _snap(active_view_id="input.faalwijzen", workspace_side="input")
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert plan.navigation.show_input_placeholder is False
    assert plan.navigation.show_input_entity_grid is True


def test_entity_grid_search_reduces_visible_rows(sample_project) -> None:
    _ensure_app()
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.faalwijzen")
    assert panel.row_count() == len(sample_project.faalwijzes)

    panel.set_search_text("FM-001")
    assert panel.visible_row_count() == 1


def test_faalwijzen_optional_aanname_columns_are_editable(sample_project) -> None:
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    row = next(r for r in svc.rows() if r.row_key == "FM-001")
    assert row.editable("aanname_faalmodel")
    assert row.editable("aanname_effectklasse")
    svc.apply_change("FM-001", "aanname_faalmodel", "Testmotivatie faalmodel")
    updated = next(r for r in svc.rows() if r.row_key == "FM-001")
    assert updated.values["aanname_faalmodel"] == "Testmotivatie faalmodel"


def test_entity_table_model_edits_optional_column(sample_project) -> None:
    from PySide6.QtCore import Qt

    from rcm_desktop.adapter.entity_grid_config import entity_grid_config_for_view
    from rcm_desktop.adapter.entity_table_model import EntityTableModel

    _ensure_app()
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    cfg = entity_grid_config_for_view("input.faalwijzen")
    assert cfg is not None
    hidden = cfg.optional_columns - {"aanname_faalmodel"}
    model = EntityTableModel(svc, sample_project, cfg, schema_columns_for_view("input.faalwijzen"), hidden_columns=hidden)
    col = model.column_ids().index("aanname_faalmodel")
    row = next(i for i in range(model.rowCount()) if model.row_key_at(i) == "FM-001")
    index = model.index(row, col)
    assert model.flags(index) & Qt.ItemFlag.ItemIsEditable
    assert model.setData(index, "Nieuwe aanname", Qt.EditRole)
    updated = next(r for r in svc.rows() if r.row_key == "FM-001")
    assert updated.values["aanname_faalmodel"] == "Nieuwe aanname"


def test_column_picker_applies_only_on_ok(sample_project) -> None:
    _ensure_app()
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.faalwijzen")
    assert "notes" in panel.hidden_columns()

    draft_hidden = frozenset({"notes"})
    checkboxes = panel._column_checkboxes_for(draft_hidden)
    checkboxes["notes"].setChecked(True)
    assert "notes" in panel.hidden_columns()

    panel.apply_column_picker_hidden(panel._hidden_from_checkboxes(checkboxes))
    assert "notes" not in panel.hidden_columns()


def test_workspace_faalwijzen_view_shows_preset_columns(sample_project) -> None:
    app = _ensure_app()
    window = ResultsWorkspaceWindow()
    window.show()
    window._state.set_last_project(sample_project)
    window.workspace_state.set_workspace_side("input")
    window.workspace_state.set_active_view("input.faalwijzen")
    app.processEvents()

    cfg = entity_grid_config_for_view("input.faalwijzen")
    assert cfg is not None
    model = window._entity_grid_panel.table_model()
    assert model is not None
    headers = [
        model.headerData(col, Qt.Orientation.Horizontal, Qt.DisplayRole)
        for col in range(model.columnCount())
    ]
    assert model.columnCount() >= len(cfg.preset_columns)
    assert "fm_id" in model.column_ids()
