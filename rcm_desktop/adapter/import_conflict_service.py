"""Resolve Isograph import conflicts (initial age per PBS), Qt-free."""

from __future__ import annotations

from collections.abc import Mapping

from rcm_core.models import RCMProject
from rcm_desktop.adapter.isograph_import_service import ImportConflict


def bouwjaar_from_age_years(modeljaar: int, age_years: float) -> int:
    return int(modeljaar - age_years)


def validate_conflict_choice(conflict: ImportConflict, chosen_age_years: float) -> bool:
    if conflict.kind != "initial_age":
        return False
    return any(abs(v - chosen_age_years) < 1e-9 for v in conflict.values)


def apply_initial_age_resolutions(
    project: RCMProject,
    *,
    modeljaar: int,
    resolutions: Mapping[str, float],
) -> None:
    """Pas gekozen initiële leeftijd (jaren) toe als `PBSItem.bouwjaar`."""
    for pbs_id, age_years in resolutions.items():
        item = project.pbs_items.get(pbs_id)
        if item is None:
            continue
        item.bouwjaar = bouwjaar_from_age_years(modeljaar, age_years)


def apply_import_conflict_choices(
    project: RCMProject,
    conflicts: list[ImportConflict],
    choices: Mapping[str, float],
    *,
    modeljaar: int,
) -> None:
    """Valideer en pas wizard-keuzes voor IA-conflicten toe."""
    by_pbs = {c.pbs_id: c for c in conflicts if c.kind == "initial_age"}
    resolutions: dict[str, float] = {}
    for pbs_id, chosen in choices.items():
        conflict = by_pbs.get(pbs_id)
        if conflict is None:
            continue
        if not validate_conflict_choice(conflict, chosen):
            raise ValueError(f"Ongeldige leeftijd voor {pbs_id}: {chosen}")
        resolutions[pbs_id] = chosen
    apply_initial_age_resolutions(project, modeljaar=modeljaar, resolutions=resolutions)
    propagate_bouwjaar_to_ancestors(project)


def propagate_bouwjaar_to_ancestors(project: RCMProject) -> None:
    """Vul ontbrekend bouwjaar op tussenliggende PBS-nodes vanuit kinderen.

    Isograph zet InitialAge op faalwijze-locaties; structurele parents hebben vaak
    geen eigen leeftijd. RCM2 vereist effectief bouwjaar > 0 op elke PBS-node.
    """
    items = project.pbs_items
    for _ in range(len(items)):
        changed = False
        for item in items.values():
            if item.bouwjaar > 0:
                continue
            child_bouwjarren = [
                items[child.pbs_id].bouwjaar
                for child in items.values()
                if child.parent_pbs_id == item.pbs_id and items[child.pbs_id].bouwjaar > 0
            ]
            if not child_bouwjarren:
                continue
            item.bouwjaar = min(child_bouwjarren)
            changed = True
        if not changed:
            break
