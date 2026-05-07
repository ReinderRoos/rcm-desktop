from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget

from rcm_core.persistence import load_project
from rcm_desktop.adapter.faalwijzen_edit_service import FaalwijzenEditService, SLICE_FIELD_KEYS
from rcm_desktop.adapter.faalwijzen_table_model import ERROR_BACKGROUND, FaalwijzenFkDelegate, FaalwijzenTableModel


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _col(name: str) -> int:
    return SLICE_FIELD_KEYS.index(name)


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def test_model_shape_flags_and_headers(sample_project):
    _ensure_app()
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    model = FaalwijzenTableModel(svc, sample_project)

    assert model.rowCount() == len(sample_project.faalwijzes)
    assert model.columnCount() == len(SLICE_FIELD_KEYS)
    fm_col = _col("fm_id")
    desc_col = _col("faalwijze_omschrijving")
    ix_fm = model.index(0, fm_col)
    ix_desc = model.index(0, desc_col)
    assert not (model.flags(ix_fm) & Qt.ItemIsEditable)
    assert model.flags(ix_desc) & Qt.ItemIsEditable


def test_display_role_fk_and_numeric_nl(sample_project):
    _ensure_app()
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    model = FaalwijzenTableModel(svc, sample_project)
    row_fm001 = next(i for i in range(model.rowCount()) if model.data(model.index(i, 0), Qt.DisplayRole) == "FM-001")
    fk_ix = model.index(row_fm001, _col("functie_id"))
    disp = model.data(fk_ix, Qt.DisplayRole)
    assert "FUNC-001" in disp
    assert "—" in disp


def test_set_data_nl_decimal_cost(sample_project):
    _ensure_app()
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    model = FaalwijzenTableModel(svc, sample_project)
    row = next(i for i in range(model.rowCount()) if model.data(model.index(i, 0), Qt.DisplayRole) == "FM-001")
    col = _col("cost_cm_eur")
    ix = model.index(row, col)
    assert model.setData(ix, "1,5", Qt.EditRole) is True
    svc_changed = svc.rows()
    fm_row = next(r for r in svc_changed if r.fm_id == "FM-001")
    assert fm_row.cost_cm_eur == pytest.approx(1.5)
    bg = model.data(ix, Qt.BackgroundRole)
    assert bg is None


def test_set_data_mttf_zero_shows_error_background_and_tooltip(sample_project):
    _ensure_app()
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    model = FaalwijzenTableModel(svc, sample_project)
    row = next(i for i in range(model.rowCount()) if model.data(model.index(i, 0), Qt.DisplayRole) == "FM-001")
    col = _col("mttf_jaar")
    ix = model.index(row, col)
    model.setData(ix, "0", Qt.EditRole)
    model.emit_grid_refresh()
    bg = model.data(ix, Qt.BackgroundRole)
    assert bg == ERROR_BACKGROUND
    tip = model.data(ix, Qt.ToolTipRole)
    assert tip is not None and "mttf" in tip.lower()
    match = next(r for r in svc.rows() if r.fm_id == "FM-001")
    assert match.field_errors["mttf_jaar"][0].code == "FM_MTTF_NONPOSITIVE"


def test_fk_delegate_clear_and_set_roundtrip(sample_project):
    _ensure_app()
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    model = FaalwijzenTableModel(svc, sample_project)
    delegate = FaalwijzenFkDelegate(sample_project)
    row = next(i for i in range(model.rowCount()) if model.data(model.index(i, 0), Qt.DisplayRole) == "FM-001")
    ix = model.index(row, _col("functie_id"))
    parent = QWidget()
    editor = delegate.createEditor(parent, None, ix)
    delegate.setEditorData(editor, ix)
    editor.setCurrentIndex(0)
    delegate.setModelData(editor, model, ix)
    model.emit_grid_refresh()
    row_v = next(r for r in svc.rows() if r.fm_id == "FM-001")
    assert row_v.functie_id == ""

    idx_known = editor.findData("FUNC-002")
    editor.setCurrentIndex(idx_known)
    delegate.setModelData(editor, model, ix)
    model.emit_grid_refresh()
    row_v2 = next(r for r in svc.rows() if r.fm_id == "FM-001")
    assert row_v2.functie_id == "FUNC-002"


def test_no_rcm_core_editing_import_in_model_module():
    import rcm_desktop.adapter.faalwijzen_table_model as m

    src = Path(m.__file__).read_text(encoding="utf-8")
    assert "rcm_core.editing" not in src
