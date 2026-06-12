"""Slice 65 — statische gates RCM-Cost parity (ADR-0008)."""

from __future__ import annotations

from pathlib import Path

ADR = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "adr"
    / "ADR-0008-rcm-cost-parity.md"
)


def test_adr_documents_parity_pass_criteria() -> None:
    source = ADR.read_text(encoding="utf-8")
    assert "TotalCost" in source
    assert "TotalCostErrPc" in source
    assert "rcm_cost_benchmark" in source


def test_parity_modules_exist() -> None:
    root = Path(__file__).resolve().parent.parent
    assert (root / "rcm_core" / "rcm_cost_benchmark.py").is_file()
    assert (root / "rcm_desktop" / "adapter" / "rcm_cost_parity_service.py").is_file()
    assert (root / "rcm_desktop" / "views" / "rcm_cost_parity_dialog.py").is_file()


def test_import_service_captures_benchmark_columns() -> None:
    service = (
        Path(__file__).resolve().parent.parent
        / "rcm_desktop"
        / "adapter"
        / "isograph_import_service.py"
    )
    source = service.read_text(encoding="utf-8")
    assert "_CAUSE_BENCHMARK_COLS" in source
    assert "_CAUSE_DIAGNOSTIC_COLS" in source
    assert '"TotalCost"' in source
    assert '"TotalTdt"' in source
    assert '"TotalW"' in source
    assert '"CTdt"' in source


def test_parity_diagnostics_module_exists() -> None:
    root = Path(__file__).resolve().parent.parent
    assert (root / "rcm_core" / "fm_parity_diagnostics.py").is_file()


def test_workspace_wires_rcm_cost_parity() -> None:
    workspace = (
        Path(__file__).resolve().parent.parent
        / "rcm_desktop"
        / "views"
        / "results_workspace_window.py"
    )
    source = workspace.read_text(encoding="utf-8")
    assert "rcm_cost_parity_button" in source
    assert "_open_rcm_cost_parity" in source
    assert "build_parity_view" in source
