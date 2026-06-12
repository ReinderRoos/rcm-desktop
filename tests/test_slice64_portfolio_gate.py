"""Slice 64 — statische gates portfolio scan + library distill (ADR-0009)."""

from __future__ import annotations

from pathlib import Path

ADR = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "adr"
    / "ADR-0009-portfolio-merge-library-scan.md"
)


def test_adr_documents_two_layer_library_and_local_scan() -> None:
    source = ADR.read_text(encoding="utf-8")
    assert "Laag A" in source
    assert "Laag B" in source
    assert "lokale map-only" in source.casefold() or "lokale map" in source
    assert "provenance" in source.casefold()


def test_portfolio_modules_exist() -> None:
    root = Path(__file__).resolve().parent.parent / "rcm_core"
    for name in (
        "portfolio_manifest.py",
        "portfolio_scan.py",
        "library_distill.py",
        "portfolio_merge.py",
        "portfolio_run.py",
    ):
        assert (root / name).is_file(), f"missing {name}"


def test_portfolio_desktop_modules_exist() -> None:
    adapter = Path(__file__).resolve().parent.parent / "rcm_desktop" / "adapter"
    views = Path(__file__).resolve().parent.parent / "rcm_desktop" / "views"
    for path in (
        adapter / "portfolio_wizard_service.py",
        adapter / "library_explorer_service.py",
        views / "portfolio_wizard_dialog.py",
        views / "library_explorer_dialog.py",
    ):
        assert path.is_file(), f"missing {path.name}"


def test_adr_documents_id_prefix_and_sidecar() -> None:
    source = ADR.read_text(encoding="utf-8")
    assert "ID-prefix" in source or "id_map" in source
    assert "portfolio_manifest" in source.casefold()


def test_bibliotheek_item_has_provenance_field() -> None:
    from rcm_core.models import BibliotheekItem

    fields = BibliotheekItem.__dataclass_fields__
    assert "provenance" in fields


def test_workspace_wires_portfolio_wizard() -> None:
    workspace = (
        Path(__file__).resolve().parent.parent
        / "rcm_desktop"
        / "views"
        / "results_workspace_window.py"
    )
    source = workspace.read_text(encoding="utf-8")
    assert "portfolio_wizard_button" in source
    assert "run_portfolio_wizard_with_root_picker" in source
    assert "_open_portfolio_wizard" in source
