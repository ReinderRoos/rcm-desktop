from __future__ import annotations
from pathlib import Path

from rcm_core.validators import ValidationError
from rcm_desktop.adapter import validate_service


def test_validate_service_happy_path_returns_valid(monkeypatch):
    fixture = Path("tests/fixtures/sample_project.rcm.json")

    monkeypatch.setattr(validate_service, "validate_project", lambda _project: [])
    monkeypatch.setattr(validate_service, "validate_aannamen", lambda _project: [])

    result, project = validate_service.run(fixture)

    assert result.status == "valid"
    assert project is not None
    assert result.error is None
    assert result.details == []


def test_validate_service_maps_warning_status(monkeypatch):
    fixture = Path("tests/fixtures/sample_project.rcm.json")

    monkeypatch.setattr(validate_service, "validate_project", lambda _project: [])
    monkeypatch.setattr(
        validate_service,
        "validate_aannamen",
        lambda _project: [ValidationError(code="WARN_1", message="Waarschuwing", context="ctx")],
    )

    result, project = validate_service.run(fixture)

    assert result.status == "valid_with_warnings"
    assert project is not None
    assert len(result.details) == 1
    assert result.details[0].severity == "warning"
    assert result.details[0].code == "WARN_1"


def test_validate_service_missing_file_returns_error():
    result, project = validate_service.run("tests/fixtures/does_not_exist.rcm.json")

    assert result.status == "error"
    assert project is None
    assert result.error is not None
    assert result.error.code == "FILE_NOT_FOUND"


def test_validate_service_invalid_json_returns_invalid(tmp_path: Path):
    invalid_json = tmp_path / "broken.rcm.json"
    invalid_json.write_text("{not-json", encoding="utf-8")

    result, project = validate_service.run(invalid_json)

    assert result.status == "invalid"
    assert project is None
    assert result.error is None
    assert result.details
    assert result.details[0].severity == "error"
    assert result.details[0].code == "PROJECT_PARSE_ERROR"


def test_validate_service_validation_errors_mapped(monkeypatch):
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    validation_errors = [ValidationError(code="FM_PBS_FK", message="pbs ontbreekt", context="FM-1")]

    monkeypatch.setattr(validate_service, "validate_project", lambda _project: validation_errors)
    monkeypatch.setattr(validate_service, "validate_aannamen", lambda _project: [])

    result, project = validate_service.run(fixture)

    assert result.status == "invalid"
    assert project is not None
    assert result.error is None
    assert len(result.details) == 1
    assert result.details[0].severity == "error"
    assert result.details[0].code == "FM_PBS_FK"
    assert result.details[0].context == "FM-1"
