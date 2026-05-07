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


def test_materialize_blocked_when_errors_remain(sample_project):
    svc = FaalwijzenEditService()
    svc.init(sample_project)
    original_mttf = sample_project.faalwijzes["FM-001"].mttf_jaar
    svc.apply_change("FM-001", "mttf_jaar", "0")
    assert svc.has_errors()
    with pytest.raises(FaalwijzenMaterializeBlockedError):
        svc.materialize_for_run()
    assert sample_project.faalwijzes["FM-001"].mttf_jaar == original_mttf


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
