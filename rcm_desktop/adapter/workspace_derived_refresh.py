"""Qt-vrije derived workspace state voor presentatie-refresh (slice 92)."""

from __future__ import annotations

from collections.abc import Sequence

from rcm_core.models import FMResult, RCMProject

from rcm_desktop.adapter.nb_effect_filter_presentation import (
    NbEffectFilterPresentation,
    build_nb_effect_filter_presentation,
)


def plan_nb_filter_refresh(
    project: RCMProject | None,
    fm_results: Sequence[FMResult] = (),
) -> NbEffectFilterPresentation:
    """Bereken NbEffectFilterPresentation uit project en run-resultaten.

    Pure functie — geen Qt vereist. Geeft een lege presentatie terug als
    ``project`` None is; anders delegeert naar ``build_nb_effect_filter_presentation``.
    """
    if project is None:
        return NbEffectFilterPresentation(entries=())
    return build_nb_effect_filter_presentation(project, fm_results)
