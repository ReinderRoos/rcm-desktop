"""Portfolio manifest contract (ADR-0009) — provenance per netwerkschakel."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

PORTFOLIO_MANIFEST_SCHEMA_VERSION = 1

WARN_LIFECYCLE_MISMATCH = "WARN_LIFECYCLE_MISMATCH"
WARN_MODELJAAR_MISMATCH = "WARN_MODELJAAR_MISMATCH"


@dataclass(frozen=True)
class PortfolioSourceEntry:
    """Eén bronmodel binnen een portfolio-scan."""

    source_id: str
    netwerkschakel_label: str
    relative_path: str
    source_type: str  # "rcm_json" | "xlsx"
    sha256: str
    mtime_ns: int
    lifecycle_years: float | None = None
    modeljaar: int | None = None
    fm_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "source_id": self.source_id,
            "netwerkschakel_label": self.netwerkschakel_label,
            "relative_path": self.relative_path,
            "source_type": self.source_type,
            "sha256": self.sha256,
            "mtime_ns": self.mtime_ns,
            "fm_count": self.fm_count,
        }
        if self.lifecycle_years is not None:
            out["lifecycle_years"] = self.lifecycle_years
        if self.modeljaar is not None:
            out["modeljaar"] = self.modeljaar
        return out

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> PortfolioSourceEntry:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class PortfolioManifest:
    """Sidecar-manifest voor samengesteld portfolio."""

    schema_version: int = PORTFOLIO_MANIFEST_SCHEMA_VERSION
    scan_root_label: str = ""
    store_absolute_paths: bool = False
    sources: list[PortfolioSourceEntry] = field(default_factory=list)
    id_map: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scan_root_label": self.scan_root_label,
            "store_absolute_paths": self.store_absolute_paths,
            "sources": [s.to_dict() for s in self.sources],
            "id_map": dict(self.id_map),
        }

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> PortfolioManifest:
        sources_raw = d.get("sources") or []
        sources = [
            PortfolioSourceEntry.from_dict(s)
            for s in sources_raw
            if isinstance(s, Mapping)
        ]
        return cls(
            schema_version=int(d.get("schema_version", PORTFOLIO_MANIFEST_SCHEMA_VERSION)),
            scan_root_label=str(d.get("scan_root_label") or ""),
            store_absolute_paths=bool(d.get("store_absolute_paths", False)),
            sources=sources,
            id_map=dict(d.get("id_map") or {}),
        )

    def lifecycle_warnings(
        self,
        *,
        relative_tolerance: float = 0.05,
    ) -> list[str]:
        """Waarschuwingen wanneer lifecycle tussen bronnen afwijkt (grill 2)."""
        lifecycles = [
            s.lifecycle_years
            for s in self.sources
            if s.lifecycle_years is not None and s.lifecycle_years > 0
        ]
        if len(lifecycles) < 2:
            return []
        lo, hi = min(lifecycles), max(lifecycles)
        if lo <= 0:
            return []
        if (hi - lo) / lo > relative_tolerance:
            return [WARN_LIFECYCLE_MISMATCH]
        return []

    def modeljaar_warnings(self) -> list[str]:
        """Waarschuwing wanneer modeljaar tussen bronnen verschilt."""
        years = {s.modeljaar for s in self.sources if s.modeljaar is not None}
        if len(years) > 1:
            return [WARN_MODELJAAR_MISMATCH]
        return []

    def all_config_warnings(
        self,
        *,
        lifecycle_relative_tolerance: float = 0.05,
    ) -> list[str]:
        return self.lifecycle_warnings(
            relative_tolerance=lifecycle_relative_tolerance
        ) + self.modeljaar_warnings()
