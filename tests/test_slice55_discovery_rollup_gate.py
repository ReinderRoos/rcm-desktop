"""Slice 55 — statische gates voor meekoppel discovery parent-rollup."""

from __future__ import annotations

from pathlib import Path

DISCOVERY = (
    Path(__file__).resolve().parent.parent
    / "rcm_desktop"
    / "adapter"
    / "meekoppelkansen_discovery_service.py"
)
PANEL = (
    Path(__file__).resolve().parent.parent
    / "rcm_desktop"
    / "adapter"
    / "meekoppel_panel_service.py"
)
ADR = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "adr"
    / "ADR-0005-meekoppelen-onderhoud.md"
)


def test_discovery_service_exports_bundling_pbs_id() -> None:
    source = DISCOVERY.read_text(encoding="utf-8")
    assert "def bundling_pbs_id(" in source
    assert "bundle_key = bundling_pbs_id(project, leaf_pbs_id)" in source


def test_discovery_buckets_on_bundling_key_not_leaf() -> None:
    source = DISCOVERY.read_text(encoding="utf-8")
    assert "MeekoppelRevTask(pm_id=task.pm_id, pbs_id=leaf_pbs_id" in source


def test_panel_scope_uses_leaf_dekking() -> None:
    source = PANEL.read_text(encoding="utf-8")
    assert "def _group_visible_in_covered(" in source
    assert "any(task.pbs_id in covered for task in row.tasks)" in source


def test_adr_documents_parent_rollup() -> None:
    source = ADR.read_text(encoding="utf-8")
    assert "slice 55" in source.casefold()
    assert "parent_pbs_id" in source
    assert "MeekoppelRevTask.pbs_id" in source
    assert "leaf-fallback" in source.casefold() or "leaf-fallback" in source
