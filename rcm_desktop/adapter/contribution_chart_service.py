"""Top 10 (Bijdragen) — aggregeer FM-scalars naar PBS- of faalwijze-rijen.



Waarde per FM komt uit `contribution_horizon_value_service` (horizon/NB-weergave).

"""

from __future__ import annotations



from collections import defaultdict

from dataclasses import dataclass



from rcm_core.effect_impact_service import EffectNbFilterSet, nb_scalar_for_fm

from rcm_core.models import RCMProject



from rcm_desktop.adapter.contribution_horizon_value_service import (
    contribution_value_for_fm,
    effect_presentation_for_contribution,
)

from rcm_desktop.adapter.result_filter_service import collect_pbs_subtree_ids

from rcm_desktop.adapter.results_workspace_state import (

    ContributionPresentation,

    METRIC_NIET_BESCHIKBAARHEID,

    SOURCE_FAALWIJZE,

    SOURCE_PBS,

)

from rcm_desktop.adapter.run_service import RunResult





@dataclass(frozen=True)

class ContributionRow:

    category_id: str

    label: str

    value: float

    share_pct: float

    eenheid: str = ""

    rf_display: str = ""





def _fm_contribution_value(

    project: RCMProject,

    fmr,

    *,

    metric: str,

    pres: ContributionPresentation,

    effect_nb_filter: EffectNbFilterSet | None,

) -> float:

    if metric == METRIC_NIET_BESCHIKBAARHEID and effect_nb_filter is not None:

        if not effect_nb_filter.is_all():

            return nb_scalar_for_fm(

                project,

                fmr,

                nb_filter=effect_nb_filter,

                presentation=effect_presentation_for_contribution(project, pres),

            )

    return contribution_value_for_fm(project, fmr, metric=metric, presentation=pres)





def build_contribution_rows(

    project: RCMProject,

    run: RunResult,

    *,

    source: str,

    metric: str,

    top_n: int,

    scope_id: str | None,

    presentation: ContributionPresentation | None = None,

    fm_ids: frozenset[str] | None = None,

    effect_nb_filter: EffectNbFilterSet | None = None,

) -> tuple[ContributionRow, ...]:

    """Top-N bijdragen na aggregatie over PBS of per faalwijze (FM-id)."""

    pres = presentation or ContributionPresentation()

    fm_results = run.fm_core_results

    if not fm_results:

        return ()



    if scope_id is None:

        scoped_fm = fm_results

    elif scope_id not in project.pbs_items:

        return ()

    else:

        subtree = collect_pbs_subtree_ids(project, scope_id)

        scoped_fm = tuple(fmr for fmr in fm_results if fmr.pbs_id in subtree)



    if fm_ids is not None:

        scoped_fm = tuple(fmr for fmr in scoped_fm if fmr.fm_id in fm_ids)



    items: list[tuple[str, str, float]]



    if source == SOURCE_PBS:

        buckets: dict[str, float] = defaultdict(float)

        for fmr in scoped_fm:

            buckets[fmr.pbs_id] += _fm_contribution_value(

                project,

                fmr,

                metric=metric,

                pres=pres,

                effect_nb_filter=effect_nb_filter,

            )

        items = []

        for pid, val in buckets.items():

            pbs_item = project.pbs_items.get(pid)

            label = pbs_item.bouwdeel_naam if pbs_item is not None else pid

            items.append((pid, label, float(val)))

    elif source == SOURCE_FAALWIJZE:

        items = []

        for fmr in scoped_fm:

            val = _fm_contribution_value(

                project,

                fmr,

                metric=metric,

                pres=pres,

                effect_nb_filter=effect_nb_filter,

            )

            pbs_item = project.pbs_items.get(fmr.pbs_id)

            bouwdeel = pbs_item.bouwdeel_naam if pbs_item is not None else fmr.pbs_id

            fm_def = project.faalwijzes.get(fmr.fm_id)

            if fm_def is not None:

                label = f"{bouwdeel} — {fm_def.faalwijze_omschrijving}"

            else:

                label = bouwdeel

            items.append((fmr.fm_id, label, float(val)))

    else:

        raise ValueError(f"Onbekende bron: {source!r}")



    total = sum(v for _, _, v in items)

    ranked = sorted(items, key=lambda t: (-t[2], t[0]))

    n = max(0, int(top_n))

    chosen = ranked[:n]



    if total <= 0.0:

        return tuple(

            ContributionRow(category_id=cid, label=lab, value=val, share_pct=0.0)

            for cid, lab, val in chosen

        )



    return tuple(

        ContributionRow(

            category_id=cid,

            label=lab,

            value=val,

            share_pct=(val / total) * 100.0,

        )

        for cid, lab, val in chosen

    )


