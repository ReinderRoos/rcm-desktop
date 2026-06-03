"""Slice 53 issue 02 — Gate 50-05 (FM-spine self-check).

Run locally:

    python -m pytest tests/test_slice53_issue02_gate50_05.py -q
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

FM_SPINE_SUBSET = [
    "tests/test_desktop_fm_edit_services.py",
    "tests/test_slice49_fm_editor_ux.py",
]

EDITING_HOST_SUBSET = [
    "tests/test_editing_host.py",
]

CHECKLIST_ADAPTER_MODULES = (
    "rcm_desktop/adapter/fm_edit_scope_loader.py",
    "rcm_desktop/adapter/fm_edit_commit_facade.py",
    "rcm_desktop/adapter/editing_host.py",
)


def _run_pytest(modules: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "pytest", *modules, "-q", "--tb=line"]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


def test_gate50_05_fm_spine_subset_is_green() -> None:
    result = _run_pytest(FM_SPINE_SUBSET)
    assert result.returncode == 0, result.stdout + result.stderr


def test_gate50_05_editing_host_subset_is_green() -> None:
    result = _run_pytest(EDITING_HOST_SUBSET)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("module_path", FM_SPINE_SUBSET + EDITING_HOST_SUBSET)
def test_gate50_05_test_modules_exist(module_path: str) -> None:
    assert (ROOT / module_path).is_file()


@pytest.mark.parametrize("adapter_path", CHECKLIST_ADAPTER_MODULES)
def test_gate50_05_checklist_adapter_modules_exist(adapter_path: str) -> None:
    assert (ROOT / adapter_path).is_file()
