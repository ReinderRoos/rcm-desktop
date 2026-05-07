"""
persistence.py — JSON opslaan/laden van RCMProject.

Primair bestandsformaat: <naam>.rcm.json
Alle modellen implementeren to_dict()/from_dict() — deze module verzorgt alleen de I/O.
"""
from __future__ import annotations

import json
from pathlib import Path

from rcm_core.models import RCMProject


def save_project(project: RCMProject, path: str | Path) -> None:
    """Sla een RCMProject op als JSON-bestand."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(project.to_dict(), f, indent=2, ensure_ascii=False)


def load_project(path: str | Path) -> RCMProject:
    """Laad een RCMProject uit een JSON-bestand."""
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return RCMProject.from_dict(data)
