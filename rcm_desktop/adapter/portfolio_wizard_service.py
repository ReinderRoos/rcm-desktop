"""Portfolio-wizard orchestratie (Qt-free, slice 64 issue 03)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rcm_core.models import RCMProject
from rcm_core.persistence import load_project, save_project
from rcm_core.portfolio_manifest import PortfolioManifest, PortfolioSourceEntry
from rcm_core.portfolio_merge import (
    PortfolioMergeResult,
    PortfolioSource,
    merge_portfolio_sources,
    save_portfolio_manifest_sidecar,
)
from rcm_core.portfolio_scan import scan_portfolio_root
from rcm_desktop import messages


@dataclass(frozen=True)
class PortfolioPreviewRow:
    source_id: str
    netwerkschakel_label: str
    relative_path: str
    source_type: str
    fm_count: int
    lifecycle_years: float | None
    modeljaar: int | None
    loadable: bool


@dataclass(frozen=True)
class PortfolioWizardPreview:
    scan_root: Path
    scan_root_label: str
    rows: tuple[PortfolioPreviewRow, ...]
    config_warnings: tuple[str, ...]
    scan_errors: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioWizardResult:
    project: RCMProject
    manifest: PortfolioManifest
    warnings: tuple[str, ...]


def _resolve_source_path(scan_root: Path, relative_path: str) -> Path:
    return (scan_root / relative_path).resolve()


def _load_row_project(scan_root: Path, row: PortfolioPreviewRow) -> RCMProject:
    path = _resolve_source_path(scan_root, row.relative_path)
    if not path.is_relative_to(scan_root.resolve()):
        raise ValueError(f"Pad valt buiten sync-root: {row.relative_path}")
    return load_project(path)


def preview_portfolio_scan(
    scan_root: Path,
    *,
    scan_root_label: str = "",
) -> PortfolioWizardPreview:
    """Scan sync-root en bouw preview-rijen voor wizard."""
    scan = scan_portfolio_root(scan_root)
    label = scan_root_label or scan.root.name
    rows: list[PortfolioPreviewRow] = []

    manifest_sources: list[PortfolioSourceEntry] = []
    for hit in scan.hits:
        loadable = hit.source_type == "rcm_json"
        fm_count = 0
        lifecycle: float | None = None
        modeljaar: int | None = None
        source_id = f"{hit.netwerkschakel_label}-{Path(hit.relative_path).stem}"

        if loadable:
            project = load_project(_resolve_source_path(scan_root, hit.relative_path))
            fm_count = len(project.faalwijzes)
            lifecycle = project.config.lifecycle_years
            modeljaar = project.config.modeljaar

        rows.append(
            PortfolioPreviewRow(
                source_id=source_id,
                netwerkschakel_label=hit.netwerkschakel_label,
                relative_path=hit.relative_path,
                source_type=hit.source_type,
                fm_count=fm_count,
                lifecycle_years=lifecycle,
                modeljaar=modeljaar,
                loadable=loadable,
            )
        )
        manifest_sources.append(
            PortfolioSourceEntry(
                source_id=source_id,
                netwerkschakel_label=hit.netwerkschakel_label,
                relative_path=hit.relative_path,
                source_type=hit.source_type,
                sha256=hit.sha256,
                mtime_ns=hit.mtime_ns,
                lifecycle_years=lifecycle,
                modeljaar=modeljaar,
                fm_count=fm_count,
            )
        )

    manifest = PortfolioManifest(
        scan_root_label=label,
        sources=manifest_sources,
    )
    config_warnings = tuple(manifest.all_config_warnings())

    return PortfolioWizardPreview(
        scan_root=scan_root,
        scan_root_label=label,
        rows=tuple(rows),
        config_warnings=config_warnings,
        scan_errors=tuple(scan.errors),
    )


def complete_portfolio_merge(
    preview: PortfolioWizardPreview,
    *,
    selected_relative_paths: list[str],
    portfolio_name: str,
) -> PortfolioWizardResult:
    """Merge geselecteerde bronnen tot portfolio."""
    selected = {p for p in selected_relative_paths}
    sources: list[PortfolioSource] = []
    warnings: list[str] = list(preview.config_warnings)

    for row in preview.rows:
        if row.relative_path not in selected:
            continue
        if not row.loadable:
            warnings.append(messages.PORTFOLIO_WIZARD_NO_RCM_JSON)
            continue
        project = _load_row_project(preview.scan_root, row)
        sources.append(
            PortfolioSource(
                source_id=row.source_id,
                netwerkschakel_label=row.netwerkschakel_label,
                project=project,
                relative_path=row.relative_path,
            )
        )

    if not sources:
        raise ValueError("Geen laadbare bronnen geselecteerd")

    merged: PortfolioMergeResult = merge_portfolio_sources(
        sources,
        portfolio_name=portfolio_name,
        scan_root_label=preview.scan_root_label,
    )
    return PortfolioWizardResult(
        project=merged.project,
        manifest=merged.manifest,
        warnings=tuple(warnings),
    )


def persist_portfolio_wizard_result(
    result: PortfolioWizardResult,
    save_path: Path,
) -> Path:
    """Schrijf portfolio `.rcm.json` + manifest-sidecar."""
    save_project(result.project, save_path)
    save_portfolio_manifest_sidecar(result.manifest, save_path)
    return save_path
