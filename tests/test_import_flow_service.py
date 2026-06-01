"""Issue 3 — import_flow_service (TDD)."""

from __future__ import annotations

from pathlib import Path

from rcm_desktop.adapter.import_flow_service import gate_workbook


def test_gate_workbook_rejects_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.xlsx"
    gate = gate_workbook(missing)
    assert gate.ok is False
    assert gate.error is not None
