"""Projectpad-resolutie voor de resultatenwerkruimte (slice 58)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rcm_core.models import RCMProject

from rcm_desktop.adapter.report_path_service import default_report_output_path


@dataclass(frozen=True)
class ResolvedProjectPath:
    file_path: Path | None

    def cache_path(self) -> Path | None:
        if self.file_path is None:
            return None
        stem = self.file_path.with_suffix("")
        return stem.with_suffix(".rcm.cache.json")

    def source_workbook_path(self) -> Path | None:
        if self.file_path is None:
            return None
        stem = self.file_path.with_suffix("")
        return stem.with_suffix(".rcm.source.xlsx")

    def default_report_output_path(self, project: RCMProject) -> Path | None:
        if self.file_path is None:
            return None
        return default_report_output_path(self.file_path, project)


def resolve_project_file_path(
    *,
    session_path: Path | None,
    path_text: str,
) -> ResolvedProjectPath:
    if session_path is not None:
        return ResolvedProjectPath(session_path)
    stripped = path_text.strip()
    if stripped:
        return ResolvedProjectPath(Path(stripped))
    return ResolvedProjectPath(None)
