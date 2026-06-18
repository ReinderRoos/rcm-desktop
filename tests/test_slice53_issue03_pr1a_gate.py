"""Slice 53 issue 03 — PR1a gate for render/bind path."""

from __future__ import annotations

from pathlib import Path

WORKSPACE_WINDOW = (
    Path(__file__).resolve().parent.parent
    / "rcm_desktop"
    / "views"
    / "results_workspace_window.py"
)


def _section(source: str, start_marker: str, end_marker: str) -> str:
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[start:end]


def test_render_bind_path_avoids_mutation_project_access() -> None:
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    render_bind = _section(
        source,
        "    def _sync_pbs_tree_for_state(self) -> None:",
        "    def _commit_active_grid_edits(self) -> bool:",
    )
    assert "loaded.core()" not in render_bind
    assert "wss.editing_project(" not in render_bind


def test_pr1a_modus_builders_delegated_to_orchestrator() -> None:
    """Slice 61 PR3: modus-builders horen in orchestrator, niet in view rerender."""
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    rerender = _section(
        source,
        "    def _rerender_detail_for_current_scope(",
        "    def _selected_fm_id_from_table(self) -> str | None:",
    )
    assert "ResultsWorkspaceOrchestrator.plan_render(" in rerender
    assert "build_fm_detail_view" not in rerender
    assert "build_bijdragen_view" not in rerender
    assert "build_lcc_view" not in rerender

