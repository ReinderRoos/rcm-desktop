"""Slice 61 PR3 — statische gates voor resultatenwerkruimte-orchestrator."""

from __future__ import annotations

from pathlib import Path

WORKSPACE_WINDOW = (
    Path(__file__).resolve().parent.parent
    / "rcm_desktop"
    / "views"
    / "results_workspace_window.py"
)

# Slice 61 PRD stretch target (widget-extractie buiten scope PR3).
WORKSPACE_WINDOW_LINE_STRETCH_TARGET = 2000
# Ratchet vóór PR3-cleanup (PR2 afgerond); PR3 moet kleiner worden.
WORKSPACE_WINDOW_LINE_BASELINE = 3076

MODUS_BUILDERS = (
    "build_fm_detail_view",
    "build_bijdragen_view",
    "build_lcc_view",
)

COMPARE_BUILDERS = (
    "build_bijdragen_compare_panels",
    "build_lcc_compare_panels",
)


def _section(source: str, start_marker: str, end_marker: str) -> str:
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[start:end]


def _render_bind_path(source: str) -> str:
    return _section(
        source,
        "    def _on_workspace_state_changed(self, snapshot: WorkspaceStateSnapshot) -> None:",
        "    def _sync_pbs_tree_for_state(self) -> None:",
    )


def _rerender_path(source: str) -> str:
    return _section(
        source,
        "    def _rerender_detail_for_current_scope(",
        "    def _selected_fm_id_from_table(self) -> str | None:",
    )


def test_workspace_window_imports_orchestrator() -> None:
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    assert "from rcm_desktop.adapter.results_workspace_orchestrator import" in source
    assert "ResultsWorkspaceOrchestrator" in source
    assert "ResultsWorkspaceOrchestrator.plan_workspace_tick(" in source
    assert "ResultsWorkspaceOrchestrator.plan_render(" in source


def test_render_bind_path_avoids_modus_builders() -> None:
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    render_bind = _render_bind_path(source)
    rerender = _rerender_path(source)
    combined = render_bind + rerender
    for name in MODUS_BUILDERS + COMPARE_BUILDERS:
        assert name not in combined, f"{name} leaked into view render/bind path"


def test_workspace_window_avoids_modus_builder_imports() -> None:
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    assert "from rcm_desktop.adapter.workspace_view_service import" not in source
    for name in MODUS_BUILDERS + COMPARE_BUILDERS:
        assert name not in source, f"{name} import or call in view"


def test_workspace_window_line_count_shrank_after_pr3_cleanup() -> None:
    line_count = len(WORKSPACE_WINDOW.read_text(encoding="utf-8").splitlines())
    assert line_count < WORKSPACE_WINDOW_LINE_BASELINE, (
        f"expected < {WORKSPACE_WINDOW_LINE_BASELINE} lines after PR3 cleanup, got {line_count}"
    )
    assert line_count <= WORKSPACE_WINDOW_LINE_BASELINE


def test_workspace_window_line_stretch_target_documented() -> None:
    """Stretch ≤2000 blijft PRD-doel; huidige monolith is groter (widget-extractie volgt)."""
    line_count = len(WORKSPACE_WINDOW.read_text(encoding="utf-8").splitlines())
    assert WORKSPACE_WINDOW_LINE_STRETCH_TARGET < line_count
