from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from rcm_core.models import RCMProject


class SaveConflictError(RuntimeError):
    """Raised when target file changed since baseline."""


@dataclass(frozen=True)
class SaveSuccess:
    path: Path
    mtime_ns: int


def current_mtime_ns(path: Path) -> int | None:
    if not path.exists():
        return None
    return path.stat().st_mtime_ns


def save_project_atomically(
    project: RCMProject,
    target_path: str | Path,
    *,
    baseline_mtime_ns: int | None = None,
    check_conflict: bool = True,
) -> SaveSuccess:
    path = Path(target_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if check_conflict and baseline_mtime_ns is not None and path.exists():
        latest_mtime = current_mtime_ns(path)
        if latest_mtime is not None and latest_mtime != baseline_mtime_ns:
            raise SaveConflictError("Bestand is extern gewijzigd sinds laden.")

    payload = _project_to_canonical_json(project)
    tmp_path = path.with_name(f"{path.name}.tmp")
    bak_path = path.with_suffix(path.suffix + ".bak")

    with open(tmp_path, "w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())

    if path.exists():
        shutil.copy2(path, bak_path)
    os.replace(tmp_path, path)
    mtime = path.stat().st_mtime_ns
    return SaveSuccess(path=path, mtime_ns=mtime)


def _project_to_canonical_json(project: RCMProject) -> str:
    return json.dumps(project.to_dict(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"

