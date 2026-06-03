"""Opties voor werkruimte-rapportgeneratie (slice 57)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReportOptions:
    output_docx_path: Path
    generate_pdf: bool = True
    scope_id: str | None = None
    nb_threshold_pct: float = 1.0
    cost_threshold_pct: float = 2.0
    include_below_threshold: bool = False
