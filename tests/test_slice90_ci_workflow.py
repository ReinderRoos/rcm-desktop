"""Slice 90 issue 01 — CI-workflow contract."""

from __future__ import annotations

from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parent
    / ".."
    / ".github"
    / "workflows"
    / "ci.yml"
).resolve()


def test_ci_workflow_exists_and_runs_pytest_without_perf() -> None:
    assert WORKFLOW.is_file(), "missing .github/workflows/ci.yml"
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "push:" in text
    assert "pull_request:" in text
    assert "pytest" in text
    assert "-m perf" in text
    assert "QT_QPA_PLATFORM" in text or "offscreen" in text
    assert "3.11" in text
