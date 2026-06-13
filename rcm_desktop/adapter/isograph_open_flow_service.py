"""End-to-end import persist: workbook gate, validate, atomic save (Qt-free)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from rcm_core.import_settings_contract import (
    SOURCE_WORKBOOK_PATH_KEY,
    merge_import_settings,
)
from rcm_core.isograph_export_contract import MUST_V1_SHEET_HEADERS, load_workbook_headers
from rcm_core.models import RCMProject

from rcm_desktop.adapter.isograph_import_wizard_service import ImportWizardResult
from rcm_desktop.adapter.project_path_resolution_service import ResolvedProjectPath
from rcm_desktop.adapter.save_service import save_project_atomically
from rcm_desktop.adapter.adapter_error_handling import user_facing_from_exception
from rcm_desktop.adapter.validate_service import UserFacingError, ValidateResult
from rcm_desktop.adapter.validation_orchestrator import validate_in_memory


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
    except Exception as exc:
        return user_facing_from_exception(
            "rcm_desktop.adapter.isograph_open_flow_service",
            code="WORKBOOK_UNREADABLE",
            message="Het bestand is geen geldige RCM-Cost Excel-export.",
            exc=exc,
            context="workbook headers lezen mislukt",
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
    return validate_in_memory(project)


def _attach_import_settings(project: RCMProject, import_settings: dict) -> None:
    project.import_settings = merge_import_settings(
        project.import_settings,
        import_settings,
    )


def _persist_source_workbook_sidecar(
    source_workbook_path: Path,
    save_path: Path,
) -> str:
    resolved = ResolvedProjectPath(save_path)
    sidecar_path = resolved.source_workbook_path()
    if sidecar_path is None:
        raise ValueError("save_path required for source workbook sidecar")
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_workbook_path, sidecar_path)
    return sidecar_path.name


def persist_import_wizard_result(
    wizard: ImportWizardResult,
    save_path: Path,
    *,
    source_workbook_path: Path | None = None,
) -> PersistImportSuccess | PersistImportFailure:
    """Valideer geïmporteerd project en sla atomisch op als .rcm.json."""
    project = wizard.project
    import_settings = dict(wizard.import_settings)
    if source_workbook_path is not None:
        import_settings[SOURCE_WORKBOOK_PATH_KEY] = _persist_source_workbook_sidecar(
            source_workbook_path,
            save_path,
        )
    _attach_import_settings(project, import_settings)

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
