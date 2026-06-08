"""Slice 53 issue 04 — PR1b: resultatenwerkruimte zonder loaded.core() in view."""

from __future__ import annotations

import re
from pathlib import Path

WORKSPACE_WINDOW = (
    Path(__file__).resolve().parent.parent
    / "rcm_desktop"
    / "views"
    / "results_workspace_window.py"
)


def test_results_workspace_view_has_no_loaded_core_calls() -> None:
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    assert "loaded.core()" not in source
    assert "_session_core" not in source


def test_results_workspace_view_does_not_import_rcm_core_models() -> None:
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    assert not re.search(r"from\s+rcm_core\.models\s+import", source)
    assert not re.search(r"import\s+rcm_core\.models", source)
