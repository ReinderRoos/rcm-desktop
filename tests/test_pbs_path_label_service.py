"""Unit tests — PBS boompad labels (slice 40)."""

from __future__ import annotations

from rcm_core.models import PBSItem, RCMProject

from rcm_desktop.adapter.pbs_path_label_service import path_label


def _project_with_chain() -> RCMProject:
    return RCMProject.from_dict(
        {
            "config": {"lifecycle_years": 40.0, "modeljaar": 2026},
            "pbs_items": {
                "ROOT": {
                    "pbs_id": "ROOT",
                    "object_naam": "",
                    "element_naam": "",
                    "bouwdeel_naam": "Installatie",
                    "component_naam": "",
                    "multiplicity": 1,
                    "bouwjaar": 2000,
                },
                "CHILD": {
                    "pbs_id": "CHILD",
                    "object_naam": "",
                    "element_naam": "",
                    "bouwdeel_naam": "Pompkamer",
                    "component_naam": "",
                    "multiplicity": 1,
                    "bouwjaar": 2000,
                    "parent_pbs_id": "ROOT",
                },
                "LEAF": {
                    "pbs_id": "LEAF",
                    "object_naam": "",
                    "element_naam": "",
                    "bouwdeel_naam": "",
                    "component_naam": "",
                    "multiplicity": 1,
                    "bouwjaar": 2000,
                    "parent_pbs_id": "CHILD",
                },
            },
            "functies": {},
            "faalwijzes": {},
            "pm_tasks": {},
            "task_groups": {},
            "effect_klassen": {},
            "fm_effect_links": {},
            "pm_effect_links": {},
            "bibliotheek": {},
        }
    )


def test_path_label_root_to_leaf():
    project = _project_with_chain()
    assert path_label(project, "LEAF") == "Installatie › Pompkamer › LEAF"


def test_path_label_single_node():
    project = _project_with_chain()
    assert path_label(project, "ROOT") == "Installatie"


def test_path_label_unknown_pbs_returns_id():
    project = _project_with_chain()
    assert path_label(project, "MISSING") == "MISSING"
