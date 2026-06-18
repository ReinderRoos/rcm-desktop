"""Slice 95 issue 03 — ADR vergelijkingsbeleid + glossary."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ADR_PATH = REPO_ROOT / "docs" / "adr" / "ADR-0016-vergelijkingsbeleid.md"
CONTEXT_PATH = REPO_ROOT / "CONTEXT.md"


def test_adr_0016_exists_and_covers_compare_policy() -> None:
    assert ADR_PATH.is_file()
    text = ADR_PATH.read_text(encoding="utf-8")
    assert "vergelijkingsbeleid" in text.lower() or "Vergelijkingsbeleid" in text
    assert "balanced" in text.lower()
    assert "twee" in text.lower() and "project" in text.lower()


def test_context_glossary_contains_slice95_terms() -> None:
    text = CONTEXT_PATH.read_text(encoding="utf-8")
    assert "vergelijkingswerkruimte" in text.lower() or "Vergelijkingswerkruimte" in text
    assert "uniformeringsvoorstel" in text.lower() or "Uniformeringsvoorstel" in text
    assert "chrome-profiel" in text.lower() or "Chrome-profiel" in text
