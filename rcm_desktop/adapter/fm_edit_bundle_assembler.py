"""Bouwt FmEditBundle uit editor-draft (Qt-vrij)."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from rcm_desktop.adapter.cm_cost_split_mapper import CmCostSplit, merge_cm_cost
from rcm_desktop.adapter.fm_edit_bundle_service import FmEditBundle
from rcm_desktop.adapter.fm_edit_row_mappers import downtime_dict_from_hours


@dataclass(frozen=True)
class FmEditDraft:
    fm_id: str
    baseline: FmEditBundle
    failure_type: str
    mttf_jaar: float
    sigma_jaar: float
    is_evident: bool
    faalwijze_omschrijving: str
    functie_id: str
    repair_quality: float
    cm_materiaal: float
    cm_arbeid: float
    downtime_hours: float
    notes: str
    aanname_cm_kosten: str
    aanname_downtime: str
    bouwjaar: int
    fm_effect_rows: tuple[dict[str, Any], ...]
    pm_task_rows: tuple[dict[str, Any], ...]
    pm_effect_rows: tuple[dict[str, Any], ...]
    effect_klasse_rows: tuple[dict[str, Any], ...]
    task_group_rows: tuple[dict[str, Any], ...]
    aging_distribution: str = "normal"
    beta_jaar: float = 0.0


def assemble_bundle(draft: FmEditDraft) -> FmEditBundle:
    faal = copy.deepcopy(draft.baseline.faalwijze_row)
    faal["failure_type"] = draft.failure_type
    faal["aging_distribution"] = draft.aging_distribution
    faal["mttf_jaar"] = draft.mttf_jaar
    faal["sigma_jaar"] = draft.sigma_jaar
    faal["beta_jaar"] = draft.beta_jaar
    faal["is_evident"] = draft.is_evident
    faal["faalwijze_omschrijving"] = draft.faalwijze_omschrijving
    faal["functie_id"] = draft.functie_id
    faal["repair_quality"] = draft.repair_quality
    faal["cost_cm_eur"] = merge_cm_cost(CmCostSplit(draft.cm_materiaal, draft.cm_arbeid))
    faal["downtime_per_failure"] = downtime_dict_from_hours(draft.downtime_hours)
    faal["notes"] = draft.notes
    faal["aanname_cm_kosten"] = draft.aanname_cm_kosten
    faal["aanname_downtime"] = draft.aanname_downtime

    pbs = copy.deepcopy(draft.baseline.pbs_row)
    pbs["bouwjaar"] = draft.bouwjaar

    return FmEditBundle(
        fm_id=draft.fm_id,
        faalwijze_row=faal,
        pbs_row=pbs,
        fm_effect_rows=draft.fm_effect_rows,
        pm_task_rows=draft.pm_task_rows,
        pm_effect_rows=draft.pm_effect_rows,
        task_group_rows=draft.task_group_rows,
        effect_klasse_rows=draft.effect_klasse_rows,
    )
