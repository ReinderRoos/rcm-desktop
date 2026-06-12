"""Slice 88 — invoerbevindingen in het entiteiten-grid."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from rcm_core.editing.state import blocking_edit_error_count, init_edit_state, validate_all_entities
from rcm_core.models import FailureType, RCMProject
from rcm_core.persistence import load_project
from rcm_core.validators import validate_project

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.entity_edit_service import EntityEditService
from rcm_desktop.adapter.entity_table_model import (
    ERROR_BACKGROUND,
    ERROR_MENU_FOREGROUND,
    WARNING_BACKGROUND,
    WARNING_FOREGROUND,
    WARNING_MENU_FOREGROUND,
    EntityFkDelegate,
    EntityTableModel,
    apply_findings_style_to_option,
    cell_background_for_errors,
    cell_foreground_for_errors,
    cell_tooltip_for_errors,
)
from rcm_desktop.adapter.entity_grid_config import entity_grid_config_for_view
from rcm_desktop.adapter.faalwijzen_edit_service import CellErrorView
from rcm_desktop.adapter.input_grid_findings import inject_input_grid_findings
from rcm_desktop.adapter.input_revalidation_service import revalidate_input_buffer
from rcm_desktop.adapter.workspace_menu_spec import WORKSPACE_MENU_SPEC
from rcm_desktop.views.panels.entity_grid_panel import EntityGridPanel


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_project() -> RCMProject:
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def _inject_warning(session: dict, entity: str, row_key: str, field: str, message: str) -> None:
    session.setdefault("edit_errors", {}).setdefault(entity, {}).setdefault(row_key, {}).setdefault(
        field,
        [],
    ).append(
        {
            "code": "TEST_WARNING",
            "severity": "warning",
            "message": message,
            "field": field,
            "row_key": row_key,
            "entity": entity,
        }
    )


def test_init_edit_state_populates_edit_errors_without_edit(sample_project) -> None:
    project = copy.deepcopy(sample_project)
    fm = project.faalwijzes["FM-001"]
    object.__setattr__(fm, "mttf_jaar", 0.0)
    session: dict = {}
    init_edit_state(project, session=session)
    errs = session["edit_errors"]["faalwijzes"].get("FM-001", {})
    assert any(e["code"] == "FM_MTTF_NONPOSITIVE" for arr in errs.values() for e in arr)


def test_blocking_error_count_ignores_warnings(sample_project) -> None:
    session: dict = {}
    init_edit_state(sample_project, session=session)
    _inject_warning(session, "faalwijzes", "FM-001", "notes", "alleen waarschuwing")
    assert blocking_edit_error_count(session) == 0


def test_entity_edit_service_exposes_severity(sample_project) -> None:
    session: dict = {}
    init_edit_state(sample_project, session=session)
    _inject_warning(session, "faalwijzes", "FM-001", "sigma_jaar", "motivatie ontbreekt")
    svc = EntityEditService.for_view("input.faalwijzen")
    editing = EditingSession(session=session)
    editing._base_project = sample_project  # noqa: SLF001
    svc.attach_editing_session(editing)
    row = next(r for r in svc.rows() if r.row_key == "FM-001")
    assert row.field_errors["sigma_jaar"][0].severity == "warning"


def test_entity_table_model_warning_and_error_backgrounds(sample_project) -> None:
    _ensure_app()
    session: dict = {}
    init_edit_state(sample_project, session=session)
    _inject_warning(session, "faalwijzes", "FM-001", "sigma_jaar", "waarschuwing")
    svc = EntityEditService.for_view("input.faalwijzen")
    editing = EditingSession(session=session)
    editing._base_project = sample_project  # noqa: SLF001
    svc.attach_editing_session(editing)
    cfg = entity_grid_config_for_view("input.faalwijzen")
    assert cfg is not None
    model = EntityTableModel(svc, sample_project, cfg, cfg.preset_columns)
    row = next(i for i in range(model.rowCount()) if model.row_key_at(i) == "FM-001")
    sigma_col = cfg.preset_columns.index("sigma_jaar")
    warn_ix = model.index(row, sigma_col)
    assert model.data(warn_ix, Qt.BackgroundRole) == WARNING_BACKGROUND
    assert model.data(warn_ix, Qt.ForegroundRole) == WARNING_FOREGROUND

    svc.apply_change("FM-001", "mttf_jaar", "0")
    model.emit_grid_refresh()
    mttf_col = cfg.preset_columns.index("mttf_jaar")
    err_ix = model.index(row, mttf_col)
    assert model.data(err_ix, Qt.BackgroundRole) == ERROR_BACKGROUND
    assert model.data(err_ix, Qt.ForegroundRole) is None


def test_error_background_wins_over_warning() -> None:
    errs = (
        CellErrorView(code="W", message="warn", severity="warning"),
        CellErrorView(code="E", message="err", severity="error"),
    )
    assert cell_background_for_errors(errs) == ERROR_BACKGROUND


def test_cell_foreground_black_for_warnings_only() -> None:
    warn_only = (CellErrorView(code="W", message="warn", severity="warning"),)
    mixed = (
        CellErrorView(code="W", message="warn", severity="warning"),
        CellErrorView(code="E", message="err", severity="error"),
    )
    assert cell_foreground_for_errors(warn_only) == WARNING_FOREGROUND
    assert cell_foreground_for_errors(mixed) is None
    assert cell_foreground_for_errors(()) is None


def test_apply_findings_style_to_option_uses_model_roles(sample_project) -> None:
    _ensure_app()
    session: dict = {}
    init_edit_state(sample_project, session=session)
    _inject_warning(session, "faalwijzes", "FM-001", "functie_id", "waarschuwing")
    svc = EntityEditService.for_view("input.faalwijzen")
    editing = EditingSession(session=session)
    editing._base_project = sample_project  # noqa: SLF001
    svc.attach_editing_session(editing)
    cfg = entity_grid_config_for_view("input.faalwijzen")
    assert cfg is not None
    model = EntityTableModel(svc, sample_project, cfg, cfg.preset_columns)
    row = next(i for i in range(model.rowCount()) if model.row_key_at(i) == "FM-001")
    functie_col = cfg.preset_columns.index("functie_id")
    index = model.index(row, functie_col)

    option = QStyleOptionViewItem()
    apply_findings_style_to_option(option, index)
    assert option.palette.color(option.palette.ColorRole.Text) == WARNING_FOREGROUND
    assert option.palette.color(option.palette.ColorRole.Base) == WARNING_BACKGROUND


def test_fk_delegate_applies_warning_foreground(sample_project) -> None:
    _ensure_app()
    session: dict = {}
    init_edit_state(sample_project, session=session)
    _inject_warning(session, "faalwijzes", "FM-001", "functie_id", "waarschuwing")
    svc = EntityEditService.for_view("input.faalwijzen")
    editing = EditingSession(session=session)
    editing._base_project = sample_project  # noqa: SLF001
    svc.attach_editing_session(editing)
    cfg = entity_grid_config_for_view("input.faalwijzen")
    assert cfg is not None
    model = EntityTableModel(svc, sample_project, cfg, cfg.preset_columns)
    row = next(i for i in range(model.rowCount()) if model.row_key_at(i) == "FM-001")
    functie_col = cfg.preset_columns.index("functie_id")
    index = model.index(row, functie_col)

    delegate = EntityFkDelegate(sample_project)
    option = QStyleOptionViewItem()
    delegate.initStyleOption(option, index)
    assert option.palette.color(option.palette.ColorRole.Text) == WARNING_FOREGROUND


def test_tooltip_groups_by_severity() -> None:
    errs = (
        CellErrorView(code="E", message="fout melding", severity="error"),
        CellErrorView(code="W", message="waarschuwing melding", severity="warning"),
    )
    tip = cell_tooltip_for_errors(errs)
    assert "fout melding" in tip
    assert "waarschuwing melding" in tip
    assert tip.index("fout melding") < tip.index("waarschuwing melding")


def test_materialize_not_blocked_by_warnings_only(sample_project) -> None:
    session: dict = {}
    init_edit_state(sample_project, session=session)
    _inject_warning(session, "faalwijzes", "FM-001", "notes", "niet blokkerend")
    svc = EntityEditService.for_view("input.faalwijzen")
    editing = EditingSession(session=session)
    editing._base_project = sample_project  # noqa: SLF001
    svc.attach_editing_session(editing)
    assert svc.has_errors() is False
    svc.materialize_for_run()


def test_workspace_menu_has_revalidate_input() -> None:
    by_id = {item.action_id: item for section in WORKSPACE_MENU_SPEC for item in section.items}
    item = by_id["analysis.revalidate_input"]
    assert item.shortcut == "F7"
    assert item.checkable is False


def test_columns_with_findings(sample_project) -> None:
    session: dict = {}
    init_edit_state(sample_project, session=session)
    _inject_warning(session, "faalwijzes", "FM-001", "sigma_jaar", "waarschuwing")
    svc = EntityEditService.for_view("input.faalwijzen")
    editing = EditingSession(session=session)
    editing._base_project = sample_project  # noqa: SLF001
    svc.attach_editing_session(editing)
    assert svc.columns_with_findings() == frozenset({"sigma_jaar"})


def test_column_findings_severity(sample_project) -> None:
    session: dict = {}
    init_edit_state(sample_project, session=session)
    _inject_warning(session, "faalwijzes", "FM-001", "sigma_jaar", "waarschuwing")
    svc = EntityEditService.for_view("input.faalwijzen")
    editing = EditingSession(session=session)
    editing._base_project = sample_project  # noqa: SLF001
    svc.attach_editing_session(editing)
    assert svc.column_findings_severity() == {"sigma_jaar": "warning"}

    svc.apply_change("FM-001", "mttf_jaar", "0")
    assert svc.column_findings_severity()["mttf_jaar"] == "error"

    session["edit_errors"]["faalwijzes"]["FM-001"]["mttf_jaar"].append(
        {
            "code": "TEST_WARNING",
            "severity": "warning",
            "message": "waarschuwing",
            "field": "mttf_jaar",
            "row_key": "FM-001",
            "entity": "faalwijzes",
        }
    )
    assert svc.column_findings_severity()["mttf_jaar"] == "error"


def test_entity_grid_panel_column_menu_bolds_findings_columns(sample_project) -> None:
    _ensure_app()
    session: dict = {}
    init_edit_state(sample_project, session=session)
    _inject_warning(session, "faalwijzes", "FM-001", "sigma_jaar", "waarschuwing")
    svc = EntityEditService.for_view("input.faalwijzen")
    editing = EditingSession(session=session)
    editing._base_project = sample_project  # noqa: SLF001
    svc.attach_editing_session(editing)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.faalwijzen")
    assert panel.column_menu_action_bold("sigma_jaar") is True
    assert panel.column_menu_action_bold("fm_id") is False


def test_entity_grid_panel_column_menu_colors_findings_columns(sample_project) -> None:
    _ensure_app()
    session: dict = {}
    init_edit_state(sample_project, session=session)
    _inject_warning(session, "faalwijzes", "FM-001", "sigma_jaar", "waarschuwing")
    svc = EntityEditService.for_view("input.faalwijzen")
    editing = EditingSession(session=session)
    editing._base_project = sample_project  # noqa: SLF001
    svc.attach_editing_session(editing)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.faalwijzen")
    assert panel.column_menu_action_foreground("sigma_jaar") == WARNING_MENU_FOREGROUND
    assert panel.column_menu_action_foreground("fm_id") is None

    svc.apply_change("FM-001", "mttf_jaar", "0")
    assert panel.column_menu_action_foreground("mttf_jaar") == ERROR_MENU_FOREGROUND


def test_entity_grid_panel_shows_findings_count(sample_project) -> None:
    _ensure_app()
    session: dict = {}
    init_edit_state(sample_project, session=session)
    _inject_warning(session, "faalwijzes", "FM-001", "sigma_jaar", "waarschuwing")
    svc = EntityEditService.for_view("input.faalwijzen")
    editing = EditingSession(session=session)
    editing._base_project = sample_project  # noqa: SLF001
    svc.attach_editing_session(editing)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.faalwijzen")
    label = panel.row_count_label_text()
    assert "waarschuwing" in label.lower()


def test_revalidate_input_buffer_refreshes_findings(sample_project) -> None:
    project = copy.deepcopy(sample_project)
    fm = project.faalwijzes["FM-001"]
    object.__setattr__(fm, "failure_type", FailureType.RANDOM)
    object.__setattr__(fm, "sigma_jaar", 5.0)
    session = EditingSession()
    session.load_project(project)
    revalidate_input_buffer(session)
    errs = session.session["edit_errors"]["faalwijzes"].get("FM-001", {})
    assert any(
        e["code"] == "FM_RANDOM_SIGMA_NONZERO" and e["severity"] == "error"
        for arr in errs.values()
        for e in arr
    )


def test_consistency_aging_without_rev_warning(sample_project) -> None:
    project = copy.deepcopy(sample_project)
    fm = project.faalwijzes["FM-001"]
    object.__setattr__(fm, "failure_type", FailureType.AGING)
    session = EditingSession()
    session.load_project(project)
    rows = copy.deepcopy(session.session["edit_current"]["pm_tasks"])
    session.session["edit_current"]["pm_tasks"] = [
        r for r in rows if r.get("fm_id") != "FM-001" or str(r.get("taak_type", "")).upper() != "REV"
    ]
    revalidate_input_buffer(session)
    errs = session.session["edit_errors"]["faalwijzes"].get("FM-001", {})
    assert any(
        e["code"] == "AGING_WITHOUT_REV" and e["severity"] == "warning"
        for arr in errs.values()
        for e in arr
    )


def test_nmf_requires_test_warning_in_grid_hard_on_validate(sample_project) -> None:
    project = copy.deepcopy(sample_project)
    fm = project.faalwijzes["FM-001"]
    object.__setattr__(fm, "is_evident", False)
    session = EditingSession()
    session.load_project(project)
    rows = copy.deepcopy(session.session["edit_current"]["pm_tasks"])
    session.session["edit_current"]["pm_tasks"] = [
        r for r in rows if not (r.get("fm_id") == "FM-001" and str(r.get("taak_type", "")).upper() in ("IN", "TST"))
    ]
    revalidate_input_buffer(session)
    grid_errs = session.session["edit_errors"]["faalwijzes"].get("FM-001", {})
    assert any(
        e["code"] == "FM_NMF_REQUIRES_TEST" and e["severity"] == "warning"
        for arr in grid_errs.values()
        for e in arr
    )
    built = session.build_project()
    assert any(e.code == "FM_NMF_REQUIRES_TEST" for e in validate_project(built))


def test_aannamen_warning_on_hidden_column_falls_back_to_key(sample_project) -> None:
    project = copy.deepcopy(sample_project)
    fm = project.faalwijzes["FM-001"]
    object.__setattr__(fm, "cost_cm_eur", 100.0)
    object.__setattr__(fm, "aanname_cm_kosten", "")
    session = EditingSession()
    session.load_project(project)
    revalidate_input_buffer(session)
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.attach_editing_session(session)
    cfg = entity_grid_config_for_view("input.faalwijzen")
    assert cfg is not None
    hidden = frozenset({"aanname_cm_kosten"})
    model = EntityTableModel(svc, project, cfg, cfg.preset_columns, hidden_columns=hidden)
    row = next(i for i in range(model.rowCount()) if model.row_key_at(i) == "FM-001")
    key_col = cfg.preset_columns.index("fm_id")
    ix = model.index(row, key_col)
    assert model.data(ix, Qt.BackgroundRole) == WARNING_BACKGROUND
