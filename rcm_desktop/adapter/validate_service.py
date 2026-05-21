from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from rcm_core.models import RCMProject
from rcm_core.persistence import load_project
from rcm_core.validators import ValidationError, validate_aannamen, validate_project


@dataclass(frozen=True)
class DetailItem:
    severity: str
    code: str
    message: str
    context: str = ""


@dataclass(frozen=True)
class UserFacingError:
    code: str
    message: str


@dataclass(frozen=True)
class ValidateResult:
    status: str
    summary: str
    details: list[DetailItem]
    error: UserFacingError | None = None


def run(project_path: str | Path) -> tuple[ValidateResult, RCMProject | None]:
    path = Path(project_path)
    try:
        project = load_project(path)
    except FileNotFoundError:
        return (
            ValidateResult(
                status="error",
                summary=f"Bestand niet gevonden: {path}",
                details=[],
                error=UserFacingError(code="FILE_NOT_FOUND", message="Het gekozen projectbestand bestaat niet."),
            ),
            None,
        )
    except (PermissionError, OSError):
        return (
            ValidateResult(
                status="error",
                summary=f"Bestand kan niet worden geopend: {path}",
                details=[],
                error=UserFacingError(code="FILE_IO_ERROR", message="Het projectbestand kon niet worden gelezen."),
            ),
            None,
        )
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        return (
            ValidateResult(
                status="invalid",
                summary="Projectbestand is ongeldig JSON of heeft een ongeldig schema.",
                details=[DetailItem(severity="error", code="PROJECT_PARSE_ERROR", message=str(exc))],
            ),
            None,
        )
    except Exception:
        return (
            ValidateResult(
                status="error",
                summary="Onverwachte fout tijdens laden van project.",
                details=[],
                error=UserFacingError(code="UNEXPECTED_ERROR", message="Er ging iets mis tijdens valideren."),
            ),
            None,
        )

    errors = validate_project(project)
    if errors:
        return (
            ValidateResult(
                status="invalid",
                summary=f"Validatie mislukt met {len(errors)} fout(en).",
                details=_to_details(errors, severity="error"),
            ),
            project,
        )

    warnings = validate_aannamen(project)
    if warnings:
        return (
            ValidateResult(
                status="valid_with_warnings",
                summary=f"Structuur geldig met {len(warnings)} waarschuwing(en).",
                details=_to_details(warnings, severity="warning"),
            ),
            project,
        )

    return (
        ValidateResult(
            status="valid",
            summary="Project is geldig.",
            details=[],
        ),
        project,
    )


def _to_details(items: list[ValidationError], severity: str) -> list[DetailItem]:
    return [
        DetailItem(
            severity=severity,
            code=item.code,
            message=item.message,
            context=item.context,
        )
        for item in items
    ]
