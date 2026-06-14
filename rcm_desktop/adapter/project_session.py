"""View-facing aggregate: loaded project path + adapter projection + last run."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.simulation_engine_service import MCRunResult


@dataclass(frozen=True)
class ProjectSession:
    """Eén seam voor resultatenwerkruimte: pad, LoadedProject en RunResult."""

    path: Path | None
    loaded: LoadedProject
    run: RunResult | None
    mc_run: MCRunResult | None = None

    @classmethod
    def from_parts(
        cls,
        loaded: LoadedProject,
        *,
        path: Path | None = None,
        run: RunResult | None = None,
        mc_run: MCRunResult | None = None,
    ) -> ProjectSession:
        return cls(path=path, loaded=loaded, run=run, mc_run=mc_run)

    def has_completed_run(self) -> bool:
        return self.run is not None and self.run.status == "done"
