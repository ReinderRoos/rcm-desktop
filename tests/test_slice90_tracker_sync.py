"""Slice 90 issue 02 — tracker-sync en .gitignore contract."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_slices_87_89_prd_triage_is_done() -> None:
    prds = (
        ROOT / ".scratch/rcm-desktop-slice87-input-grid-filter-performance/PRD.md",
        ROOT / ".scratch/rcm-desktop-slice88-invoerbevindingen-grid/PRD.md",
        ROOT / ".scratch/rcm-desktop-slice89-bufferbrede-dirty-seam/PRD.md",
    )
    for prd in prds:
        text = prd.read_text(encoding="utf-8")
        assert "done" in text
        assert "ready-for-agent" not in text


def test_gitignore_covers_generated_cache_and_bak() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("*.cache.*.json", "*.rcm.json.bak"):
        assert pattern in gitignore
