"""Slice 66 issue 03 — KANBAN-handoff en config-defaults."""

from __future__ import annotations

from pathlib import Path

from rcm_core.config import RCMConfig

SLICE66_DIR = (
    Path(__file__).resolve().parents[1]
    / ".scratch/rcm-desktop-slice66-rev-segment-survival-fix"
)
KANBAN_HANDOFF = SLICE66_DIR / "KANBAN_HANDOFF.md"


def test_slice66_kanban_handoff_exists() -> None:
    assert KANBAN_HANDOFF.is_file(), "KANBAN_HANDOFF.md must exist (issue 03 deliverable)"


def test_slice66_kanban_handoff_documents_reproducible_parity_check() -> None:
    text = KANBAN_HANDOFF.read_text(encoding="utf-8")
    assert "build_parity_report" in text
    assert "RCMCostdata export_Gaarkeuken.rcm.json" in text
    assert "test_gaarkeuken_parity_gate" in text


def test_slice66_kanban_handoff_documents_root_cause_and_baseline() -> None:
    text = KANBAN_HANDOFF.read_text(encoding="utf-8")
    assert "128" in text and "135" in text
    assert "survival" in text.lower()
    assert "ADR-0008" in text
    assert "slice 65" in text.lower() or "slice 52" in text.lower()


def test_aw_mc_lifecycle_horizon_default_is_true() -> None:
    assert RCMConfig().aw_mc_lifecycle_horizon is True
