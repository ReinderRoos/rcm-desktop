from __future__ import annotations

from pathlib import Path
import time

import pytest

from rcm_core.persistence import load_project
from rcm_desktop.adapter.save_service import SaveConflictError, save_project_atomically


def test_save_project_atomically_writes_and_creates_bak(tmp_path: Path):
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    target = tmp_path / "project.rcm.json"
    target.write_text('{"old": true}\n', encoding="utf-8")
    baseline = target.stat().st_mtime_ns

    saved = save_project_atomically(project, target, baseline_mtime_ns=baseline, check_conflict=True)

    assert saved.path == target
    assert target.exists()
    bak = target.with_suffix(".json.bak")
    assert bak.exists()
    assert '"faalwijzes"' in target.read_text(encoding="utf-8")


def test_save_project_atomically_raises_conflict_on_external_change(tmp_path: Path):
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    target = tmp_path / "project.rcm.json"
    target.write_text('{"v": 1}\n', encoding="utf-8")
    baseline = target.stat().st_mtime_ns
    time.sleep(0.02)
    target.write_text('{"v": 2}\n', encoding="utf-8")

    with pytest.raises(SaveConflictError):
        save_project_atomically(project, target, baseline_mtime_ns=baseline, check_conflict=True)
