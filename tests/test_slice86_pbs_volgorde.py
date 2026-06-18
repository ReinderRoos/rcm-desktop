"""Slice 86 — PBS-volgorde, navigatie/reorder-sneltoetsen, ADR."""

from __future__ import annotations

import copy

import pytest

from rcm_core.cache import compute_global_digest, compute_fm_hash
from rcm_core.config import RCMConfig
from rcm_core.models import PBSItem, RCMProject, Faalwijze
from rcm_core.persistence import load_project
from rcm_desktop.adapter.pbs_order_service import (
    sibling_pbs_ids_sorted,
    swap_pbs_sibling_order,
)
from rcm_desktop.adapter.rcm_navigation_tree_builder import build_rcm_navigation_tree
from rcm_desktop.adapter.workspace_menu_spec import WORKSPACE_MENU_SPEC


def _two_siblings(*, vol_a: int = 0, vol_b: int = 1) -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=5.0, modeljaar=2020),
        pbs_items={
            "PBS-A": PBSItem(
                "PBS-A", "o", "e", "Brug", parent_pbs_id=None, volgorde=vol_a
            ),
            "PBS-B": PBSItem(
                "PBS-B", "o", "e", "Schutsluis", parent_pbs_id=None, volgorde=vol_b
            ),
        },
    )


def test_volgorde_round_trip_via_to_dict() -> None:
    project = _two_siblings()
    restored = RCMProject.from_dict(project.to_dict())
    assert restored.pbs_items["PBS-A"].volgorde == 0
    assert restored.pbs_items["PBS-B"].volgorde == 1


def test_only_volgorde_change_does_not_change_digests() -> None:
    before = _two_siblings()
    before.faalwijzes["FM-1"] = Faalwijze(
        fm_id="FM-1",
        pbs_id="PBS-A",
        functie_id="F",
        faalwijze_omschrijving="x",
        mttf_jaar=10.0,
    )
    after = copy.deepcopy(before)
    after.pbs_items["PBS-A"].volgorde = 99
    after.pbs_items["PBS-B"].volgorde = -1
    assert compute_global_digest(before) == compute_global_digest(after)
    assert compute_fm_hash(before, "FM-1") == compute_fm_hash(after, "FM-1")


def test_rekenveld_change_does_change_digest() -> None:
    before = _two_siblings()
    after = copy.deepcopy(before)
    after.pbs_items["PBS-A"].bouwdeel_naam = "Brug gewijzigd"
    assert compute_global_digest(before) != compute_global_digest(after)


def test_migration_assigns_read_order_when_volgorde_missing(tmp_path) -> None:
    raw = {
        "config": {"lifecycle_years": 5.0, "modeljaar": 2020},
        "pbs_items": {
            "PBS-A": {
                "pbs_id": "PBS-A",
                "object_naam": "o",
                "element_naam": "e",
                "bouwdeel_naam": "Eerste",
            },
            "PBS-B": {
                "pbs_id": "PBS-B",
                "object_naam": "o",
                "element_naam": "e",
                "bouwdeel_naam": "Tweede",
            },
        },
    }
    path = tmp_path / "test.rcm.json"
    import json

    path.write_text(json.dumps(raw), encoding="utf-8")
    project = load_project(path)
    order = sibling_pbs_ids_sorted(project, parent_pbs_id=None)
    assert order == ("PBS-A", "PBS-B")


def test_sibling_sort_uses_volgorde() -> None:
    project = _two_siblings(vol_a=1, vol_b=0)
    assert sibling_pbs_ids_sorted(project, parent_pbs_id=None) == ("PBS-B", "PBS-A")


def test_swap_exchanges_neighbor_volgorde() -> None:
    project = _two_siblings()
    swapped, changed = swap_pbs_sibling_order(project, "PBS-A", direction="down")
    assert changed is True
    assert swapped.pbs_items["PBS-A"].volgorde == 1
    assert swapped.pbs_items["PBS-B"].volgorde == 0


def test_swap_at_boundary_is_noop() -> None:
    project = _two_siblings()
    result, changed = swap_pbs_sibling_order(project, "PBS-A", direction="up")
    assert changed is False
    assert result.pbs_items["PBS-A"].volgorde == 0


def test_navigation_tree_follows_volgorde() -> None:
    project = _two_siblings(vol_a=1, vol_b=0)
    roots = build_rcm_navigation_tree(project)
    assert [n.node_id for n in roots] == ["PBS-B", "PBS-A"]


def test_menu_spec_includes_pbs_navigation_shortcuts() -> None:
    action_ids = {
        item.action_id
        for section in WORKSPACE_MENU_SPEC
        for item in section.items
    }
    assert "view.pbs_move_up" in action_ids
    assert "view.pbs_move_down" in action_ids
    assert "view.pbs_select_prev_sibling" in action_ids
    assert "view.pbs_select_next_sibling" in action_ids
    assert "view.pbs_select_parent" in action_ids
    assert "view.pbs_select_first_child" in action_ids
