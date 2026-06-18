"""Dual-project compare session (slice 95 issue 04)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rcm_core.models import RCMProject
from rcm_core.persistence import load_project


@dataclass(frozen=True)
class CompareSession:
    path_a: Path
    path_b: Path
    project_a: RCMProject
    project_b: RCMProject


def load_compare_session(path_a: Path | str, path_b: Path | str) -> CompareSession:
    resolved_a = Path(path_a)
    resolved_b = Path(path_b)
    if not resolved_a.is_file():
        raise FileNotFoundError(f"Project A not found: {resolved_a}")
    if not resolved_b.is_file():
        raise FileNotFoundError(f"Project B not found: {resolved_b}")
    return CompareSession(
        path_a=resolved_a,
        path_b=resolved_b,
        project_a=load_project(resolved_a),
        project_b=load_project(resolved_b),
    )
