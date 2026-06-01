"""Qt-vrije import open-flow orchestration (slice 41, ADR-0004)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from rcm_core.models import RCMProject

from rcm_desktop.adapter.isograph_import_wizard_service import ImportWizardResult
from rcm_desktop.adapter.isograph_open_flow_service import (
    PersistImportFailure,
    PersistImportSuccess,
    check_workbook_importable,
    persist_import_wizard_result,
)
from rcm_desktop.adapter.validate_service import UserFacingError, ValidateResult


@dataclass(frozen=True)
class ImportGateResult:
    ok: bool
    error: UserFacingError | None = None


@dataclass(frozen=True)
class ImportPersistResult:
    kind: Literal["success", "blocked"]
    success: PersistImportSuccess | None = None
    failure: PersistImportFailure | None = None

    @property
    def validate_result(self) -> ValidateResult | None:
        if self.success is not None:
            return self.success.validate_result
        if self.failure is not None:
            return self.failure.validate_result
        return None

    @property
    def project(self) -> RCMProject | None:
        if self.success is not None:
            return self.success.project
        return None


def gate_workbook(path: Path) -> ImportGateResult:
    error = check_workbook_importable(path)
    if error is not None:
        return ImportGateResult(ok=False, error=error)
    return ImportGateResult(ok=True)


def persist_wizard_result(
    wizard: ImportWizardResult,
    save_path: Path,
) -> ImportPersistResult:
    outcome = persist_import_wizard_result(wizard, save_path)
    if isinstance(outcome, PersistImportSuccess):
        return ImportPersistResult(kind="success", success=outcome)
    return ImportPersistResult(kind="blocked", failure=outcome)
