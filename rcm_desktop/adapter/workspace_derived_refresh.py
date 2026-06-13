"""Qt-vrije derived workspace state voor presentatie-refresh (slice 92)."""

from __future__ import annotations

from collections.abc import Sequence

from rcm_core.models import FMResult, RCMProject

from rcm_desktop.adapter.contribution_horizon_value_service import (
    calendar_years_for_project,
)
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


def plan_contribution_year_refresh(project: RCMProject | None) -> tuple[int, ...]:
    """Bereken kalenderjaren voor de bijdragen-jaarkiezer uit een project.

    Pure functie — geen Qt vereist. Lege tuple als ``project`` None is.
    """
    if project is None:
        return ()
    return calendar_years_for_project(project)
