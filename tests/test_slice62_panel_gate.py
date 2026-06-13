"""Slice 62 — statische gates voor werkruimte-panel-extractie."""

from __future__ import annotations

from pathlib import Path

WORKSPACE_WINDOW = (
    Path(__file__).resolve().parent.parent
    / "rcm_desktop"
    / "views"
    / "results_workspace_window.py"
)
PANELS_DIR = (
    Path(__file__).resolve().parent.parent / "rcm_desktop" / "views" / "panels"
)
CONTEXT = Path(__file__).resolve().parent.parent / "CONTEXT.md"

WORKSPACE_WINDOW_LINE_STRETCH_TARGET = 2000
# Ratchet na slice 90 top10-extractie; 2734 regels + 10 marge.
WORKSPACE_WINDOW_LINE_BASELINE = 2744
# Vóór slice 62 PR0 (3033 regels); cumulatieve shrink-gate.
SLICE62_START_LINE_BASELINE = 3033


def test_bijdragen_panel_module_exists() -> None:
    panel = PANELS_DIR / "bijdragen_workspace_panel.py"
    assert panel.is_file()
    source = panel.read_text(encoding="utf-8")
    assert "build_bijdragen_workspace_panel" in source
    assert "BijdragenWorkspacePanel" in source


def test_workspace_window_uses_bijdragen_panel() -> None:
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    assert "from rcm_desktop.views.panels.bijdragen_workspace_panel import" in source
    assert "build_bijdragen_workspace_panel()" in source
    assert "def _build_bijdragen_page" in source
    assert "ContributionBarChartWidget()" not in source


def test_orphan_adapter_shims_removed() -> None:
    adapter = Path(__file__).resolve().parent.parent / "rcm_desktop" / "adapter"
    assert not (adapter / "dirty_session_coordinator.py").exists()
    assert not (adapter / "isograph_import_dialog.py").exists()
    assert not (adapter / "run_decision.py").exists()


def test_fm_detail_panel_module_exists() -> None:
    panel = PANELS_DIR / "fm_detail_workspace_panel.py"
    assert panel.is_file()
    source = panel.read_text(encoding="utf-8")
    assert "build_fm_detail_workspace_panel" in source
    assert "FmDetailWorkspacePanel" in source


def test_workspace_window_uses_fm_detail_panel() -> None:
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    assert "from rcm_desktop.views.panels.fm_detail_workspace_panel import" in source
    assert "build_fm_detail_workspace_panel()" in source
    assert "def _build_fm_detail_page" in source
    assert "FMResultsSortProxy(" not in source


def test_lcc_panel_module_exists() -> None:
    panel = PANELS_DIR / "lcc_workspace_panel.py"
    assert panel.is_file()
    source = panel.read_text(encoding="utf-8")
    assert "build_lcc_workspace_panel" in source
    assert "LccWorkspacePanel" in source


def test_workspace_window_uses_lcc_panel() -> None:
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    assert "from rcm_desktop.views.panels.lcc_workspace_panel import" in source
    assert "build_lcc_workspace_panel()" in source
    assert "def _build_lcc_page" in source
    assert "LCCStackedBarChartWidget()" not in source
    assert "build_lcc_compare_column(" not in source


def test_workspace_table_policy_module_exists() -> None:
    policy = PANELS_DIR / "workspace_table_policy.py"
    assert policy.is_file()
    source = policy.read_text(encoding="utf-8")
    assert "apply_workspace_data_table_header_policy" in source


def test_all_workspace_panel_modules_exist() -> None:
    expected = (
        "bijdragen_workspace_panel.py",
        "fm_detail_workspace_panel.py",
        "lcc_workspace_panel.py",
        "pbs_sidebar_panel.py",
        "top10_subbar_panel.py",
    )
    for name in expected:
        assert (PANELS_DIR / name).is_file(), f"missing panel module {name}"


def test_pbs_sidebar_panel_module_exists() -> None:
    panel = PANELS_DIR / "pbs_sidebar_panel.py"
    assert panel.is_file()
    source = panel.read_text(encoding="utf-8")
    assert "build_pbs_sidebar_panel" in source
    assert "PBSSidebarFilterProxy" in source


def test_top10_subbar_panel_module_exists() -> None:
    panel = PANELS_DIR / "top10_subbar_panel.py"
    assert panel.is_file()
    source = panel.read_text(encoding="utf-8")
    assert "build_top10_subbar_panel" in source


def test_workspace_window_line_count_shrank_after_slice62() -> None:
    line_count = len(WORKSPACE_WINDOW.read_text(encoding="utf-8").splitlines())
    assert line_count < WORKSPACE_WINDOW_LINE_BASELINE, (
        f"expected < {WORKSPACE_WINDOW_LINE_BASELINE} lines after slice 62, got {line_count}"
    )
    assert line_count < SLICE62_START_LINE_BASELINE, (
        f"expected cumulative shrink below {SLICE62_START_LINE_BASELINE}, got {line_count}"
    )


def test_workspace_window_line_stretch_target_documented() -> None:
    line_count = len(WORKSPACE_WINDOW.read_text(encoding="utf-8").splitlines())
    assert WORKSPACE_WINDOW_LINE_STRETCH_TARGET < line_count


def test_context_documents_orchestrator_terms() -> None:
    source = CONTEXT.read_text(encoding="utf-8")
    for term in (
        "ResultsWorkspaceOrchestrator",
        "WorkspaceTickPlan",
        "WorkspaceUiSyncPlan",
        "RenderPlan",
    ):
        assert term in source, f"missing orchestrator term {term!r} in CONTEXT.md"


def test_context_documents_workspace_panels() -> None:
    source = CONTEXT.read_text(encoding="utf-8")
    for term in (
        "BijdragenWorkspacePanel",
        "FmDetailWorkspacePanel",
        "LccWorkspacePanel",
    ):
        assert term in source, f"missing panel term {term!r} in CONTEXT.md"
