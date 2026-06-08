"""Slice 53 issue 01 — reconcile gate for sessie A/B/C and slices 51/52.

Run the full gate locally:

    python -m pytest tests/test_slice53_issue01_reconcile_gate.py -q
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

RECONCILE_GATE = [
    "tests/test_workspace_modus_ui_ab.py",
    "tests/test_haarlem_fixture_import_ready.py",
    "tests/test_desktop_fm_edit_services.py",
    "tests/test_slice49_fm_editor_ux.py",
    "tests/test_slice52_modelinstellingen.py",
    "tests/test_slice51_aging_distributions.py",
]


def test_reconcile_gate_pytest_subset_is_green() -> None:
    cmd = [sys.executable, "-m", "pytest", *RECONCILE_GATE, "-q", "--tb=line"]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("module_path", RECONCILE_GATE)
def test_reconcile_gate_modules_exist(module_path: str) -> None:
    assert (ROOT / module_path).is_file()
