from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.persistence import load_project
from rcm_desktop.adapter.entity_edit_service import EntityEditService, EntityRowView
from rcm_desktop.adapter.faalwijzen_grid_contract import EDITABLE_FIELDS, READONLY_FIELDS
from rcm_desktop.adapter.tabular_edit_types import MaterializeBlockedError


def _svc(changed=None) -> EntityEditService:
    return EntityEditService.for_view("input.faalwijzen", changed=changed)


def _row(rows: list[EntityRowView], fm_id: str) -> EntityRowView:
    return next(r for r in rows if r.row_key == fm_id)


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def test_init_populates_slice_rows(sample_project):
    svc = _svc()
    svc.init(sample_project)
    rows = svc.rows()
    assert len(rows) == len(sample_project.faalwijzes)
    first = _row(rows, "FM-001")
    assert first.values["pbs_id"] == "PBS-001-1"
    assert first.values["mttf_jaar"] == 15.0
    assert first.field_errors == {}


def test_editable_flags_on_slice_fields(sample_project):
    svc = _svc()
    svc.init(sample_project)
    row = svc.rows()[0]
    for name in READONLY_FIELDS:
        assert row.editable(name) is False
    for name in EDITABLE_FIELDS:
        assert row.editable(name) is True


def test_apply_change_updates_valid_mttf(sample_project):
    svc = _svc()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "20")
    row = _row(svc.rows(), "FM-001")
    assert row.values["mttf_jaar"] == 20.0
    assert not svc.has_errors()


def test_apply_change_mttf_zero_reports_fm_mttf_nonpositive(sample_project):
    svc = _svc()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "0")
    row = _row(svc.rows(), "FM-001")
    assert "mttf_jaar" in row.field_errors
    assert row.field_errors["mttf_jaar"][0].code == "FM_MTTF_NONPOSITIVE"
    assert svc.has_errors()
    assert svc.error_count() >= 1


def test_apply_change_unknown_functie_fk_error(sample_project):
    svc = _svc()
    svc.init(sample_project)
    svc.apply_change("FM-001", "functie_id", "UNKNOWN-FUNC")
    row = _row(svc.rows(), "FM-001")
    assert "functie_id" in row.field_errors
    assert row.field_errors["functie_id"][0].code == "FK_CHECK"
    assert svc.has_errors()


def test_apply_change_nl_decimal_cost_cm_eur(sample_project):
    svc = _svc()
    svc.init(sample_project)
    svc.apply_change("FM-001", "cost_cm_eur", "1,5")
    row = _row(svc.rows(), "FM-001")
    assert row.values["cost_cm_eur"] == pytest.approx(1.5)
    assert svc.has_errors() is False


def test_apply_change_faalwijze_text_accepted(sample_project):
    svc = _svc()
    svc.init(sample_project)
    svc.apply_change("FM-001", "faalwijze_omschrijving", "Testtekst met § en <symbols>")
    row = _row(svc.rows(), "FM-001")
    assert row.values["faalwijze_omschrijving"] == "Testtekst met § en <symbols>"


def test_apply_change_faalwijze_text_no_errors(sample_project):
    svc = _svc()
    svc.init(sample_project)
    svc.apply_change("FM-001", "faalwijze_omschrijving", "Andere omschrijving")
    row = _row(svc.rows(), "FM-001")
    assert row.field_errors.get("faalwijze_omschrijving") is None
    assert not svc.has_errors()


def test_materialize_returns_new_project_with_updates(sample_project):
    svc = _svc()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "99")
    built = svc.materialize_for_run()
    assert built is not sample_project
    assert built.faalwijzes["FM-001"].mttf_jaar == pytest.approx(99.0)


def test_materialize_for_save_matches_run_after_valid_edit(sample_project):
    svc = _svc()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "42")
    from_run = svc.materialize_for_run()
    from_save = svc.materialize_for_save()
    assert from_save.faalwijzes["FM-001"].mttf_jaar == pytest.approx(42.0)
    assert from_save.faalwijzes["FM-001"].mttf_jaar == from_run.faalwijzes["FM-001"].mttf_jaar


def test_materialize_blocked_when_errors_remain(sample_project):
    svc = _svc()
    svc.init(sample_project)
    original_mttf = sample_project.faalwijzes["FM-001"].mttf_jaar
    svc.apply_change("FM-001", "mttf_jaar", "0")
    assert svc.has_errors()
    with pytest.raises(MaterializeBlockedError):
        svc.materialize_for_run()
    assert sample_project.faalwijzes["FM-001"].mttf_jaar == original_mttf


def test_materialize_for_save_blocked_when_errors_remain(sample_project):
    svc = _svc()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "0")
    with pytest.raises(MaterializeBlockedError):
        svc.materialize_for_save()


def test_reset_restores_original_state(sample_project):
    svc = _svc()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "3")
    assert _row(svc.rows(), "FM-001").values["mttf_jaar"] == 3.0

    svc.reset(sample_project)
    row = _row(svc.rows(), "FM-001")
    assert row.values["mttf_jaar"] == 15.0


def test_changed_callback_after_apply(sample_project):
    calls = []

    def cb():
        calls.append(1)

    svc = _svc(changed=cb)
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "16")
    assert len(calls) == 1


def test_unknown_fm_id_no_callback(sample_project):
    calls = []

    svc = _svc(changed=lambda: calls.append(1))
    svc.init(sample_project)
    svc.apply_change("DOES-NOT-EXIST", "mttf_jaar", "10")
    assert calls == []


def test_edit_dirty_global_tracks_buffer(sample_project):
    svc = _svc()
    svc.init(sample_project)
    session = svc.editing_session.session
    assert session.get("edit_dirty_global") is False
    svc.apply_change("FM-001", "mttf_jaar", "16")
    assert session.get("edit_dirty_global") is True
    svc.apply_change("FM-001", "mttf_jaar", "15")
    assert session.get("edit_dirty_global") is False


def test_apply_bulk_change_failure_type_on_two_fms(sample_project):
    svc = _svc()
    svc.init(sample_project)
    result = svc.apply_bulk_change(["FM-001", "FM-002"], "failure_type", "aging")
    assert result.ok is True
    assert result.applied_count == 2
    for fm_id in ("FM-001", "FM-002"):
        row = _row(svc.rows(), fm_id)
        assert row.values["failure_type"] == "aging"


def test_apply_bulk_change_blocked_on_invalid_mttf(sample_project):
    svc = _svc()
    svc.init(sample_project)
    before = _row(svc.rows(), "FM-001").values["mttf_jaar"]
    result = svc.apply_bulk_change(["FM-001"], "mttf_jaar", "0")
    assert result.ok is False
    assert result.applied_count == 0
    after = _row(svc.rows(), "FM-001").values["mttf_jaar"]
    assert after == before


def test_apply_bulk_change_is_evident_nmf(sample_project):
    svc = _svc()
    svc.init(sample_project)
    result = svc.apply_bulk_change(["FM-003"], "is_evident", False)
    assert result.ok is True
    row = _row(svc.rows(), "FM-003")
    assert row.values["is_evident"] is False


def test_editable_includes_failure_type_and_nmf(sample_project):
    svc = _svc()
    svc.init(sample_project)
    row = svc.rows()[0]
    assert row.editable("failure_type") is True
    assert row.editable("is_evident") is True


def test_reset_clears_edit_dirty_global(sample_project):
    svc = _svc()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "18")
    assert svc.editing_session.session.get("edit_dirty_global") is True
    svc.reset(sample_project)
    assert svc.editing_session.session.get("edit_dirty_global") is False
