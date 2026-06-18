"""Slice 90 issue 03 — exception-keten in adapter-foutpaden."""

from __future__ import annotations

import logging
from pathlib import Path

from rcm_core.persistence import load_project
from rcm_desktop.adapter import run_service, validate_service
from rcm_desktop.adapter.adapter_error_handling import user_facing_from_exception


def test_run_service_internal_error_preserves_cause_and_logs(caplog, monkeypatch) -> None:
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    boom = RuntimeError("boom")

    def fake_raise(*_args, **_kwargs):
        raise boom

    monkeypatch.setattr(run_service, "run_incremental_analysis", fake_raise)

    with caplog.at_level(logging.ERROR, logger="rcm_desktop.adapter.run_service"):
        result = run_service.run(project, fixture)

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "RUN_INTERNAL_ERROR"
    assert result.error.__cause__ is boom
    assert any("boom" in rec.message or "boom" in (rec.exc_text or "") for rec in caplog.records)


def test_validate_service_unexpected_load_error_preserves_cause(caplog, monkeypatch, tmp_path) -> None:
    path = tmp_path / "broken.rcm.json"
    path.write_text("{}",encoding="utf-8")
    boom = RuntimeError("parse boom")

    monkeypatch.setattr(validate_service, "load_project", lambda _p: (_ for _ in ()).throw(boom))

    with caplog.at_level(logging.ERROR, logger="rcm_desktop.adapter.validate_service"):
        result, project = validate_service.run(path)

    assert project is None
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "UNEXPECTED_ERROR"
    assert result.error.__cause__ is boom


def test_user_facing_from_exception_sets_cause_and_logs(caplog) -> None:
    exc = RuntimeError("diag")
    with caplog.at_level(logging.ERROR, logger="rcm_desktop.adapter.test"):
        err = user_facing_from_exception(
            "rcm_desktop.adapter.test",
            code="TEST",
            message="Testfout",
            exc=exc,
            context="test context",
        )
    assert err.code == "TEST"
    assert err.message == "Testfout"
    assert err.__cause__ is exc
    assert caplog.records
