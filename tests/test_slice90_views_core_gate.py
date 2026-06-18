"""Slice 90 issue 08 — geen runtime rcm_core-imports in views."""

from __future__ import annotations

import ast
from pathlib import Path

VIEWS_DIR = Path(__file__).resolve().parents[1] / "rcm_desktop" / "views"


def _runtime_rcm_core_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "rcm_core" or alias.name.startswith("rcm_core."):
                    found.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == "rcm_core" or node.module.startswith("rcm_core.")):
                if node.level == 0:
                    found.append(f"from {node.module} import ...")
    return found


def test_views_have_no_runtime_rcm_core_imports() -> None:
    offenders: list[str] = []
    for path in sorted(VIEWS_DIR.rglob("*.py")):
        rel = path.relative_to(VIEWS_DIR)
        hits = _runtime_rcm_core_imports(path)
        if hits:
            offenders.append(f"{rel}: {', '.join(hits)}")
    assert offenders == [], "runtime rcm_core imports in views:\n" + "\n".join(offenders)
