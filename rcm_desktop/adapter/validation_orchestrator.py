"""Unified validation entry for file-based and in-memory projects (slice 41)."""

from __future__ import annotations

from pathlib import Path

from rcm_core.models import RCMProject
from rcm_core.validators import ValidationError, validate_aannamen, validate_project

from rcm_desktop.adapter.validate_service import DetailItem, ValidateResult, run as validate_from_path


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


def validate_in_memory(project: RCMProject) -> ValidateResult:
    """Zelfde statussen als validate_service.run, zonder bestand te laden."""
    errors = validate_project(project)
    if errors:
        return ValidateResult(
            status="invalid",
            summary=f"Validatie mislukt met {len(errors)} fout(en).",
            details=_to_details(errors, severity="error"),
        )

    warnings = validate_aannamen(project)
    if warnings:
        return ValidateResult(
            status="valid_with_warnings",
            summary=f"Structuur geldig met {len(warnings)} waarschuwing(en).",
            details=_to_details(warnings, severity="warning"),
        )

    return ValidateResult(
        status="valid",
        summary="Project is geldig.",
        details=[],
    )


def validate_path(project_path: str | Path) -> tuple[ValidateResult, RCMProject | None]:
    return validate_from_path(project_path)
