"""Adapter projection of a loaded RCM project for UI layers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rcm_core.models import RCMProject


@dataclass(frozen=True)
class LoadedProject:
    """Read-only adapter view; views importeren dit i.p.v. `RCMProject` direct."""

    project_id: str
    lifecycle_years: float
    modeljaar: int
    fm_count: int
    pbs_count: int
    pm_count: int
    _core: RCMProject

    @classmethod
    def from_core(cls, project: RCMProject, *, path: Path | None = None) -> LoadedProject:
        return cls(
            project_id=str(path) if path is not None else "local",
            lifecycle_years=float(project.config.lifecycle_years),
            modeljaar=int(project.config.modeljaar),
            fm_count=len(project.faalwijzes),
            pbs_count=len(project.pbs_items),
            pm_count=len(project.pm_tasks),
            _core=project,
        )

    def core(self) -> RCMProject:
        """Motor/adapter entry — alleen via expliciete seam."""
        return self._core
