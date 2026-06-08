"""Standaard paden voor rapportexport (slice 57)."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from rcm_core.models import RCMProject


def _safe_filename_part(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "_", name.strip())
    return cleaned or "rapport"


def default_report_output_path(project_path: Path, project: RCMProject) -> Path:
    label = project.projectnaam.strip() or project_path.stem
    safe = _safe_filename_part(label)
    folder = project_path.parent / "rapporten"
    return folder / f"{safe}_{date.today().isoformat()}.docx"
