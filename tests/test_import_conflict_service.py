"""Issue 06 — initial-age conflict resolution (Qt-free)."""

from rcm_core.config import RCMConfig
from rcm_core.models import PBSItem, RCMProject
from rcm_desktop.adapter.import_conflict_service import (
    apply_initial_age_resolutions,
    bouwjaar_from_age_years,
    propagate_bouwjaar_to_ancestors,
    validate_conflict_choice,
)
from rcm_desktop.adapter.isograph_import_service import ImportConflict


def test_bouwjaar_from_age_years() -> None:
    assert bouwjaar_from_age_years(2026, 1.0) == 2025


def test_apply_initial_age_resolutions_updates_pbs() -> None:
    project = RCMProject(
        config=RCMConfig(modeljaar=2026),
        pbs_items={"L2": PBSItem("L2", "o", "e", "Sub", bouwjaar=0)},
    )
    apply_initial_age_resolutions(
        project, modeljaar=2026, resolutions={"L2": 2.0}
    )
    assert project.pbs_items["L2"].bouwjaar == 2024


def test_propagate_bouwjaar_to_ancestors_fills_parent_from_child() -> None:
    project = RCMProject(
        config=RCMConfig(modeljaar=2026),
        pbs_items={
            "L1": PBSItem("L1", "o", "e", "Root", bouwjaar=0),
            "L2": PBSItem("L2", "o", "e", "Leaf", parent_pbs_id="L1", bouwjaar=2020),
        },
    )
    propagate_bouwjaar_to_ancestors(project)
    assert project.pbs_items["L1"].bouwjaar == 2020
    assert project.pbs_items["L1"].effective_bouwjaar(project.pbs_items) == 2020


def test_validate_conflict_choice_rejects_unknown_value() -> None:
    conflict = ImportConflict(
        pbs_id="L2", kind="initial_age", values=(1.0, 2.0)
    )
    assert validate_conflict_choice(conflict, 1.0) is True
    assert validate_conflict_choice(conflict, 3.0) is False
