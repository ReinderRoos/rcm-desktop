"""Orchestratie import-wizard: modeljaar + IA-conflicten (Qt-free)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from rcm_core.models import RCMProject
from rcm_desktop.adapter.import_conflict_service import (
    apply_import_conflict_choices,
    propagate_bouwjaar_to_ancestors,
)
from rcm_desktop.adapter.isograph_import_service import (
    ImportBuildResult,
    ImportConflict,
    build_from_workbook,
)


@dataclass(frozen=True)
class ImportWizardResult:
    project: RCMProject
    import_settings: dict
    warnings: tuple[str, ...]


def initial_age_conflicts(result: ImportBuildResult) -> tuple[ImportConflict, ...]:
    return tuple(c for c in result.conflicts if c.kind == "initial_age")


def preview_import(path: Path, *, modeljaar: int) -> ImportBuildResult:
    """Bouw project uit Excel; conflicten nog niet opgelost door de gebruiker."""
    return build_from_workbook(path, modeljaar=modeljaar)


def complete_import(
    build_result: ImportBuildResult,
    *,
    modeljaar: int,
    conflict_choices: Mapping[str, float] | None = None,
) -> ImportWizardResult:
    """Pas modeljaar en optionele IA-keuzes toe; retourneer finaal project."""
    project = build_result.project
    project.config.modeljaar = int(modeljaar)
    if conflict_choices:
        apply_import_conflict_choices(
            project,
            build_result.conflicts,
            conflict_choices,
            modeljaar=modeljaar,
        )
    else:
        propagate_bouwjaar_to_ancestors(project)
    return ImportWizardResult(
        project=project,
        import_settings=dict(build_result.import_settings),
        warnings=tuple(build_result.warnings),
    )


def import_from_excel(
    path: Path,
    *,
    modeljaar: int,
    conflict_choices: Mapping[str, float] | None = None,
) -> ImportWizardResult:
    """Eén-staps import na wizard-invoer."""
    preview = preview_import(path, modeljaar=modeljaar)
    return complete_import(
        preview, modeljaar=modeljaar, conflict_choices=conflict_choices
    )
