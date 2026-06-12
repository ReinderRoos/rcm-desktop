"""Qt-vrij presentatieplan voor NB-effectfilter (slice 85)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from rcm_core.effect_impact_service import (
    EffectNbFilterSet,
    EffectPresentation,
    HIDDEN_NB_RESTPOST_ID,
    list_nb_effect_klassen,
    nb_scalar_for_fm,
)
from rcm_core.effect_taxonomy import CATEGORIE_KOSTEN
from rcm_core.models import FMResult, RCMProject

from rcm_desktop import messages

_EPS = 1e-12
_LIFECYCLE = EffectPresentation(horizon="lifecycle")


@dataclass(frozen=True)
class NbEffectFilterEntry:
    klasse_id: str
    label: str
    selectable: bool
    disabled_reason: str | None = None


@dataclass(frozen=True)
class NbEffectFilterPresentation:
    entries: tuple[NbEffectFilterEntry, ...]


def build_nb_effect_filter_presentation(
    project: RCMProject,
    fm_results: Sequence[FMResult],
    *,
    scope_id: str | None = None,
) -> NbEffectFilterPresentation:
    """Bepaal selecteerbaarheid per NB-effectklasse over de totale PBS.

    ``scope_id`` wordt genegeerd voor bijdrage-bepaling (totale PBS); parameter
    bestaat alleen voor expliciete tests dat boomselectie geen invloed heeft.
    """
    _ = scope_id
    entries: list[NbEffectFilterEntry] = []
    for klasse_id, label in list_nb_effect_klassen(project):
        selectable = _klasse_has_contribution(project, fm_results, klasse_id)
        reason = None if selectable else messages.WORKSPACE_NB_EFFECT_FILTER_DISABLED_REASON
        entries.append(
            NbEffectFilterEntry(
                klasse_id=klasse_id,
                label=label,
                selectable=selectable,
                disabled_reason=reason,
            )
        )
    return NbEffectFilterPresentation(entries=tuple(entries))


def _klasse_has_contribution(
    project: RCMProject,
    fm_results: Sequence[FMResult],
    klasse_id: str,
) -> bool:
    faalmomenten, downtime, kosten = _total_contributions(project, fm_results, klasse_id)
    return faalmomenten > _EPS or downtime > _EPS or kosten > _EPS


def _total_contributions(
    project: RCMProject,
    fm_results: Sequence[FMResult],
    klasse_id: str,
) -> tuple[float, float, float]:
    faalmomenten = 0.0
    downtime = 0.0
    kosten = 0.0
    filt = EffectNbFilterSet(selected_klasse_ids=frozenset({klasse_id}))
    for fmr in fm_results:
        if klasse_id != HIDDEN_NB_RESTPOST_ID:
            faalmomenten += float(fmr.fm_effect_bijdragen.get(klasse_id, 0.0))
            faalmomenten += float(fmr.pm_effect_bijdragen.get(klasse_id, 0.0))
            ek = project.effect_klassen.get(klasse_id)
            if ek is not None and CATEGORIE_KOSTEN in ek.categorie.lower():
                kosten += float(fmr.fm_effect_bijdragen.get(klasse_id, 0.0))
                kosten += float(fmr.pm_effect_bijdragen.get(klasse_id, 0.0))
        downtime += float(
            nb_scalar_for_fm(project, fmr, nb_filter=filt, presentation=_LIFECYCLE)
        )
    return faalmomenten, downtime, kosten
