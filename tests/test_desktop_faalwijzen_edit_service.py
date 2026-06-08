from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.persistence import load_project
from rcm_desktop.adapter.faalwijzen_edit_service import (
    EDITABLE_FIELDS,
    READONLY_FIELDS,
    FaalwijzenEditService,
    FaalwijzenMaterializeBlockedError,
)


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def test_init_populates_slice_rows(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    rows = svc.rows()
    assert len(rows) == len(sample_project.faalwijzes)
    first = next(r for r in rows if r.fm_id == "FM-001")
    assert first.pbs_id == "PBS-001-1"
    assert first.mttf_jaar == 15.0
    assert first.field_errors == {}


def test_editable_flags_on_slice_fields(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    row = svc.rows()[0]
    for name in READONLY_FIELDS:
        assert row.editable(name) is False
    for name in EDITABLE_FIELDS:
        assert row.editable(name) is True


def test_apply_change_updates_valid_mttf(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "20")
    row = next(r for r in svc.rows() if r.fm_id == "FM-001")
    assert row.mttf_jaar == 20.0
    assert not svc.has_errors()


def test_apply_change_mttf_zero_reports_fm_mttf_nonpositive(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "0")
    row = next(r for r in svc.rows() if r.fm_id == "FM-001")
    assert "mttf_jaar" in row.field_errors
    assert row.field_errors["mttf_jaar"][0].code == "FM_MTTF_NONPOSITIVE"
    assert svc.has_errors()
    assert svc.error_count() >= 1


def test_apply_change_unknown_functie_fk_error(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    svc.apply_change("FM-001", "functie_id", "UNKNOWN-FUNC")
    row = next(r for r in svc.rows() if r.fm_id == "FM-001")
    assert "functie_id" in row.field_errors
    assert row.field_errors["functie_id"][0].code == "FK_CHECK"
    assert svc.has_errors()


def test_apply_change_nl_decimal_cost_cm_eur(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    svc.apply_change("FM-001", "cost_cm_eur", "1,5")
    row = next(r for r in svc.rows() if r.fm_id == "FM-001")
    assert row.cost_cm_eur == pytest.approx(1.5)
    assert svc.has_errors() is False


def test_apply_change_faalwijze_text_accepted(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    svc.apply_change("FM-001", "faalwijze_omschrijving", "Testtekst met § en <symbols>")
    row = next(r for r in svc.rows() if r.fm_id == "FM-001")
    assert row.faalwijze_omschrijving == "Testtekst met § en <symbols>"


def test_apply_change_faalwijze_text_no_errors(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    svc.apply_change("FM-001", "faalwijze_omschrijving", "Andere omschrijving")
    row = next(r for r in svc.rows() if r.fm_id == "FM-001")
    assert row.field_errors.get("faalwijze_omschrijving") is None
    assert not svc.has_errors()


def test_materialize_returns_new_project_with_updates(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "99")
    built = svc.materialize_for_run()
    assert built is not sample_project
    assert built.faalwijzes["FM-001"].mttf_jaar == pytest.approx(99.0)


def test_materialize_for_save_matches_run_after_valid_edit(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "42")
    from_run = svc.materialize_for_run()
    from_save = svc.materialize_for_save()
    assert from_save.faalwijzes["FM-001"].mttf_jaar == pytest.approx(42.0)
    assert from_save.faalwijzes["FM-001"].mttf_jaar == from_run.faalwijzes["FM-001"].mttf_jaar


def test_materialize_blocked_when_errors_remain(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    original_mttf = sample_project.faalwijzes["FM-001"].mttf_jaar
    svc.apply_change("FM-001", "mttf_jaar", "0")
    assert svc.has_errors()
    with pytest.raises(FaalwijzenMaterializeBlockedError):
        svc.materialize_for_run()
    assert sample_project.faalwijzes["FM-001"].mttf_jaar == original_mttf


def test_materialize_for_save_blocked_when_errors_remain(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "0")
    with pytest.raises(FaalwijzenMaterializeBlockedError):
        svc.materialize_for_save()


def test_reset_restores_original_state(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "3")
    assert next(r for r in svc.rows() if r.fm_id == "FM-001").mttf_jaar == 3.0

    svc.reset(sample_project)
    row = next(r for r in svc.rows() if r.fm_id == "FM-001")
    assert row.mttf_jaar == 15.0


def test_changed_callback_after_apply(sample_project):
    calls = []

    def cb():
        calls.append(1)

    svc = FaalwijzenEditService(changed=cb)
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "16")
    assert len(calls) == 1


def test_unknown_fm_id_no_callback(sample_project):
    calls = []

    svc = FaalwijzenEditService(changed=lambda: calls.append(1))
    svc.init(sample_project)
    svc.apply_change("DOES-NOT-EXIST", "mttf_jaar", "10")
    assert calls == []


def test_dirty_tracks_baseline_deviation(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    assert svc.is_dirty() is False
    svc.apply_change("FM-001", "mttf_jaar", "16")
    assert svc.is_dirty() is True
    svc.apply_change("FM-001", "mttf_jaar", "15")
    assert svc.is_dirty() is False


def test_apply_bulk_change_failure_type_on_two_fms(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    result = svc.apply_bulk_change(["FM-001", "FM-002"], "failure_type", "aging")
    assert result.ok is True
    assert result.applied_count == 2
    for fm_id in ("FM-001", "FM-002"):
        row = next(r for r in svc.rows() if r.fm_id == fm_id)
        assert row.failure_type == "aging"


def test_apply_bulk_change_blocked_on_invalid_mttf(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    before = next(r for r in svc.rows() if r.fm_id == "FM-001").mttf_jaar
    result = svc.apply_bulk_change(["FM-001"], "mttf_jaar", "0")
    assert result.ok is False
    assert result.applied_count == 0
    after = next(r for r in svc.rows() if r.fm_id == "FM-001").mttf_jaar
    assert after == before


def test_apply_bulk_change_is_evident_nmf(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    result = svc.apply_bulk_change(["FM-003"], "is_evident", False)
    assert result.ok is True
    row = next(r for r in svc.rows() if r.fm_id == "FM-003")
    assert row.is_evident is False


def test_editable_includes_failure_type_and_nmf(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    row = svc.rows()[0]
    assert row.editable("failure_type") is True
    assert row.editable("is_evident") is True


def test_mark_saved_resets_dirty_baseline(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    svc.apply_change("FM-001", "mttf_jaar", "18")
    assert svc.is_dirty() is True
    svc.mark_saved()
    assert svc.is_dirty() is False
