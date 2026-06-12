"""Qt-vrije RCM-Cost export-flow (slice 77 issue 04)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from rcm_core.import_settings_contract import SOURCE_WORKBOOK_PATH_KEY, merge_import_settings
from rcm_core.models import RCMProject

from rcm_desktop.adapter.isograph_export_service import (
    IsographExportResult,
    export_project_to_workbook,
    resolve_source_workbook_path,
)
from rcm_desktop.adapter.project_path_resolution_service import ResolvedProjectPath


@dataclass(frozen=True)
class ExportFlowBlocked:
    code: str
    message: str


@dataclass(frozen=True)
class ExportFlowSuccess:
    result: IsographExportResult
    source_workbook_path: Path


ExportFlowOutcome = ExportFlowSuccess | ExportFlowBlocked


def attach_located_source_workbook(
    project: RCMProject,
    project_file_path: Path,
    located_source_path: Path,
) -> Path:
    sidecar = ResolvedProjectPath(project_file_path).source_workbook_path()
    if sidecar is None:
        raise ValueError("project_file_path required")
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(located_source_path, sidecar)
    project.import_settings = merge_import_settings(
        project.import_settings,
        {SOURCE_WORKBOOK_PATH_KEY: sidecar.name},
    )
    return sidecar


def export_rcm_cost_project(
    project: RCMProject,
    *,
    project_file_path: Path | None,
    output_path: Path,
    located_source_path: Path | None = None,
) -> ExportFlowOutcome:
    if project_file_path is None:
        return ExportFlowBlocked(
            code="NO_PROJECT_PATH",
            message="Sla het project eerst op voordat u exporteert.",
        )
    source = resolve_source_workbook_path(project_file_path, project.import_settings)
    if source is None and located_source_path is not None:
        source = attach_located_source_workbook(
            project,
            project_file_path,
            located_source_path,
        )
    if source is None or not source.is_file():
        return ExportFlowBlocked(
            code="MISSING_SOURCE_WORKBOOK",
            message="De AW-bron-workbook ontbreekt.",
        )
    result = export_project_to_workbook(project, source, output_path)
    return ExportFlowSuccess(result=result, source_workbook_path=source)
