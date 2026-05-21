"""End-to-end import persist: workbook gate, validate, atomic save (Qt-free)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rcm_core.import_settings_contract import merge_import_settings
from rcm_core.isograph_export_contract import MUST_V1_SHEET_HEADERS, load_workbook_headers
from rcm_core.models import RCMProject
from rcm_core.validators import ValidationError, validate_aannamen, validate_project
from rcm_desktop.adapter.isograph_import_wizard_service import ImportWizardResult
from rcm_desktop.adapter.save_service import save_project_atomically
from rcm_desktop.adapter.validate_service import DetailItem, UserFacingError, ValidateResult


@dataclass(frozen=True)
class PersistImportSuccess:
    save_path: Path
    validate_result: ValidateResult
    project: RCMProject


@dataclass(frozen=True)
class PersistImportFailure:
    code: str
    message: str
    validate_result: ValidateResult | None = None


def check_workbook_importable(path: Path) -> UserFacingError | None:
    """Controleer leesbaarheid en must-v1 tabbladen/kolommen."""
    try:
        headers = load_workbook_headers(path)
    except (OSError, PermissionError):
        return UserFacingError(
            code="FILE_IO_ERROR",
            message="Het Excel-bestand kon niet worden gelezen.",
        )
    except Exception:
        return UserFacingError(
            code="WORKBOOK_UNREADABLE",
            message="Het bestand is geen geldige RCM-Cost Excel-export.",
        )

    missing_sheets = sorted(set(MUST_V1_SHEET_HEADERS) - set(headers))
    if missing_sheets:
        return UserFacingError(
            code="MISSING_SHEET",
            message=(
                "De export mist verplichte tabbladen: "
                + ", ".join(missing_sheets)
                + "."
            ),
        )

    for sheet, required in MUST_V1_SHEET_HEADERS.items():
        present = set(headers.get(sheet, ()))
        missing_cols = [c for c in required if c not in present]
        if missing_cols:
            return UserFacingError(
                code="MISSING_COLUMNS",
                message=(
                    f"Tabblad '{sheet}' mist kolommen: "
                    + ", ".join(missing_cols)
                    + "."
                ),
            )
    return None


def validate_project_in_memory(project: RCMProject) -> ValidateResult:
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


def _attach_import_settings(project: RCMProject, import_settings: dict) -> None:
    project.import_settings = merge_import_settings(
        project.import_settings,
        import_settings,
    )


def persist_import_wizard_result(
    wizard: ImportWizardResult,
    save_path: Path,
) -> PersistImportSuccess | PersistImportFailure:
    """Valideer geïmporteerd project en sla atomisch op als .rcm.json."""
    project = wizard.project
    _attach_import_settings(project, wizard.import_settings)

    validate_result = validate_project_in_memory(project)
    if validate_result.status == "invalid":
        return PersistImportFailure(
            code="VALIDATION_FAILED",
            message=validate_result.summary,
            validate_result=validate_result,
        )

    save_project_atomically(project, save_path, check_conflict=False)
    return PersistImportSuccess(
        save_path=Path(save_path),
        validate_result=validate_result,
        project=project,
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
