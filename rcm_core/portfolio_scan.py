"""Lokale portfolio-mapscan met path-hardening (ADR-0009, grill 5)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from rcm_core.portfolio_manifest import PortfolioManifest, PortfolioSourceEntry

MAX_SCAN_DEPTH = 2
MAX_FILE_BYTES = 50 * 1024 * 1024
RCM_JSON_SUFFIX = ".rcm.json"
XLSX_SUFFIX = ".xlsx"
RCM_COST_XLSX_PATTERN = re.compile(r"^RCMCostdata export_.*\.xlsx$", re.IGNORECASE)

_SOURCE_ID_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class PortfolioScanHit:
    """Gevonden bronbestand tijdens scan."""

    netwerkschakel_label: str
    relative_path: str
    source_type: str
    sha256: str
    mtime_ns: int
    absolute_path: Path | None = None


@dataclass
class PortfolioScanResult:
    root: Path
    store_absolute_paths: bool
    hits: list[PortfolioScanHit] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_manifest(self, *, scan_root_label: str = "") -> PortfolioManifest:
        sources: list[PortfolioSourceEntry] = []
        for hit in self.hits:
            source_id = _slug_source_id(hit.netwerkschakel_label, hit.relative_path)
            sources.append(
                PortfolioSourceEntry(
                    source_id=source_id,
                    netwerkschakel_label=hit.netwerkschakel_label,
                    relative_path=hit.relative_path,
                    source_type=hit.source_type,
                    sha256=hit.sha256,
                    mtime_ns=hit.mtime_ns,
                )
            )
        return PortfolioManifest(
            scan_root_label=scan_root_label or self.root.name,
            store_absolute_paths=self.store_absolute_paths,
            sources=sources,
        )


def _slug_source_id(netwerkschakel: str, relative_path: str) -> str:
    base = netwerkschakel.strip() or Path(relative_path).stem
    slug = _SOURCE_ID_SAFE.sub("-", base).strip("-")
    return slug or "source"


def _assert_under_root(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if not resolved.is_relative_to(root_resolved):
        raise ValueError(f"Pad valt buiten scan-root: {path}")
    return resolved


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _classify_model_file(name: str) -> str | None:
    lower = name.lower()
    if lower.endswith(RCM_JSON_SUFFIX):
        return "rcm_json"
    if lower.endswith(XLSX_SUFFIX) and RCM_COST_XLSX_PATTERN.match(name):
        return "xlsx"
    return None


def _read_netwerkschakel_label(schakel_dir: Path) -> str:
    yaml_path = schakel_dir / "netwerkschakel.yaml"
    if yaml_path.is_file() and not yaml_path.is_symlink():
        try:
            text = yaml_path.read_text(encoding="utf-8")
        except OSError:
            return schakel_dir.name
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("label:"):
                return stripped.split(":", 1)[1].strip().strip("'\"")
    return schakel_dir.name


def _scan_file(
    path: Path,
    *,
    root: Path,
    netwerkschakel_label: str,
    store_absolute_paths: bool,
    errors: list[str],
) -> PortfolioScanHit | None:
    try:
        resolved = _assert_under_root(path, root)
    except ValueError as exc:
        errors.append(str(exc))
        return None

    if resolved.is_symlink():
        errors.append(f"Symlink overgeslagen: {path}")
        return None

    if not resolved.is_file():
        return None

    source_type = _classify_model_file(resolved.name)
    if source_type is None:
        return None

    try:
        size = resolved.stat().st_size
    except OSError as exc:
        errors.append(f"Kan bestand niet lezen: {resolved} ({exc})")
        return None

    if size > MAX_FILE_BYTES:
        errors.append(
            f"Bestand te groot (>{MAX_FILE_BYTES} bytes): {resolved.relative_to(root.resolve())}"
        )
        return None

    try:
        sha = _file_sha256(resolved)
        stat = resolved.stat()
    except OSError as exc:
        errors.append(f"Hash/stat mislukt voor {resolved}: {exc}")
        return None

    rel = resolved.relative_to(root.resolve()).as_posix()
    return PortfolioScanHit(
        netwerkschakel_label=netwerkschakel_label,
        relative_path=rel,
        source_type=source_type,
        sha256=sha,
        mtime_ns=stat.st_mtime_ns,
        absolute_path=resolved if store_absolute_paths else None,
    )


def scan_portfolio_root(
    root: Path,
    *,
    store_absolute_paths: bool = False,
    max_depth: int = MAX_SCAN_DEPTH,
) -> PortfolioScanResult:
    """Scan sync-root: root → netwerkschakel-mappen → modelbestanden.

    Diepte 0 = root; diepte 1 = netwerkschakel-submap; diepte 2 = modelbestanden
    direct in die submap (geen diepere recursie).
    """
    result = PortfolioScanResult(
        root=root,
        store_absolute_paths=store_absolute_paths,
    )

    if max_depth < 1:
        result.errors.append("max_depth moet ≥ 1 zijn")
        return result

    try:
        root_resolved = root.resolve()
    except OSError as exc:
        result.errors.append(f"Ongeldige root: {root} ({exc})")
        return result

    if not root_resolved.is_dir():
        result.errors.append(f"Root is geen map: {root}")
        return result

    # Diepte 1: netwerkschakel-mappen
    try:
        schakel_dirs = sorted(
            p for p in root_resolved.iterdir() if p.is_dir() and not p.is_symlink()
        )
    except OSError as exc:
        result.errors.append(f"Kan root niet lezen: {exc}")
        return result

    for schakel_dir in schakel_dirs:
        label = _read_netwerkschakel_label(schakel_dir)
        try:
            entries = sorted(schakel_dir.iterdir())
        except OSError as exc:
            result.errors.append(f"Kan map niet lezen: {schakel_dir} ({exc})")
            continue

        for entry in entries:
            if entry.is_symlink():
                result.errors.append(f"Symlink overgeslagen: {entry}")
                continue
            hit = _scan_file(
                entry,
                root=root_resolved,
                netwerkschakel_label=label,
                store_absolute_paths=store_absolute_paths,
                errors=result.errors,
            )
            if hit is not None:
                result.hits.append(hit)

    return result
