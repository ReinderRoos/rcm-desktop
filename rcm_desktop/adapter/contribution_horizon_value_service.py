"""Scalar Top 10-waarden per FM met horizon- en weergave-keuzes (slice 33).

Levert per `FMResult` één getal voor aggregatie in `contribution_chart_service`.
Geen Qt-imports.
"""
from __future__ import annotations

from rcm_core.effect_impact_service import (
    EffectNbFilterSet,
    EffectPresentation,
    horizon_index_for_calendar_year,
    nb_scalar_for_fm,
)
from rcm_core.lcc_profile import ltap_horizon_bucket_count
from rcm_core.models import FMResult, RCMProject

from rcm_desktop.adapter.calendar_year import calendar_year_for_horizon_index
from rcm_desktop.adapter.horizon_bucket_series import (
    faalmomenten_per_bucket,
    motor_cor_eur_per_bucket,
)
from rcm_desktop.adapter.results_workspace_state import (
    ContributionPresentation,
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
)

_HOURS_PER_YEAR = 8760.0


def kosten_scalar_for_fm(
    project: RCMProject,
    fmr: FMResult,
    presentation: ContributionPresentation,
) -> float:
    if presentation.horizon == "lifecycle":
        return float(fmr.total_cost_eur)
    num = _bucket_count(project)
    cm_buckets = motor_cor_eur_per_bucket(fmr, num)
    if not cm_buckets:
        return float(fmr.total_cost_eur) / max(num, 1)
    faal_buckets = faalmomenten_per_bucket(project, fmr)
    faal_sum = float(sum(faal_buckets)) or 1.0
    pm_total = float(fmr.pm_cost_eur)
    cost_buckets = [
        float(cm_buckets[h]) + pm_total * (float(faal_buckets[h]) / faal_sum)
        for h in range(len(cm_buckets))
    ]
    if presentation.year_choice == "average":
        return float(sum(cost_buckets)) / len(cost_buckets)
    idx = _horizon_index_for_calendar_year(project, int(presentation.year_choice))
    if idx is None or idx >= len(cost_buckets):
        return 0.0
    return float(cost_buckets[idx])


def contribution_value_for_fm(
    project: RCMProject,
    fmr: FMResult,
    *,
    metric: str,
    presentation: ContributionPresentation,
) -> float:
    """Scalar waarde voor één FM in Top 10-aggregatie."""
    if metric == METRIC_KOSTEN:
        return kosten_scalar_for_fm(project, fmr, presentation)
    if metric == METRIC_FAALMOMENTEN:
        return _faalmomenten_scalar(project, fmr, presentation)
    if metric == METRIC_NIET_BESCHIKBAARHEID:
        return _unavailability_scalar(project, fmr, presentation)
    raise ValueError(f"Onbekende metric: {metric!r}")


def _bucket_count(project: RCMProject) -> int:
    return ltap_horizon_bucket_count(float(project.config.lifecycle_years))


def _horizon_index_for_calendar_year(project: RCMProject, calendar_year: int) -> int | None:
    modeljaar = int(project.config.modeljaar)
    idx = int(calendar_year) - modeljaar
    num = _bucket_count(project)
    if 0 <= idx < num:
        return idx
    return None


def _faalmomenten_scalar(
    project: RCMProject,
    fmr: FMResult,
    presentation: ContributionPresentation,
) -> float:
    if presentation.horizon == "lifecycle":
        return float(fmr.expected_failures)
    buckets = faalmomenten_per_bucket(project, fmr)
    if not buckets:
        return 0.0
    # Scale the analytical bucket distribution to fmr.expected_failures.
    # For analytical FMResult: expected_failures ≈ sum(buckets) → scale ≈ 1 (no change).
    # For MC compare slots: expected_failures is the slot-specific MC P50, but buckets
    # are rebuilt from the live project (shared by both slots) → scale corrects the mismatch
    # so each slot's display reflects its own MC run instead of the live-project analytical total.
    bucket_total = float(sum(buckets))
    expected = float(fmr.expected_failures)
    scale = expected / bucket_total if bucket_total > 0.0 else 1.0
    if presentation.year_choice == "average":
        return expected / len(buckets)
    idx = _horizon_index_for_calendar_year(project, int(presentation.year_choice))
    if idx is None:
        return 0.0
    return float(buckets[idx]) * scale


def effect_presentation_for_contribution(
    project: RCMProject,
    pres: ContributionPresentation,
) -> EffectPresentation:
    """Map de Top 10-presentation naar de NB-spine-presentation.

    Cruciaal (Bug 1): "Ø per jaar" (``year_choice == "average"``) blijft een
    per-jaar/gemiddelde-intentie en mag NIET worden platgeslagen naar
    ``lifecycle`` — anders levert het gefilterde pad het levensduur-totaal i.p.v.
    het jaargemiddelde (~60×).
    """
    if pres.horizon == "lifecycle":
        return EffectPresentation(
            horizon="lifecycle",
            unavailability_display=pres.unavailability_display,
        )
    if pres.year_choice == "average":
        return EffectPresentation(
            horizon="per_year",
            year_index=None,
            unavailability_display=pres.unavailability_display,
        )
    if isinstance(pres.year_choice, int):
        idx = horizon_index_for_calendar_year(project, int(pres.year_choice))
        return EffectPresentation(
            horizon="per_year",
            year_index=idx,
            unavailability_display=pres.unavailability_display,
        )
    return EffectPresentation(
        horizon="lifecycle",
        unavailability_display=pres.unavailability_display,
    )


def _unavailability_scalar(
    project: RCMProject,
    fmr: FMResult,
    presentation: ContributionPresentation,
) -> float:
    """Totale NB-scalar via de gedeelde NB-bucketreeks-spine (lege filter)."""
    return nb_scalar_for_fm(
        project,
        fmr,
        nb_filter=EffectNbFilterSet(),
        presentation=effect_presentation_for_contribution(project, presentation),
    )


def calendar_years_for_project(project: RCMProject) -> tuple[int, ...]:
    """Kalenderjaren in de lifecycle-horizon (voor jaarkiezer)."""
    num = _bucket_count(project)
    modeljaar = int(project.config.modeljaar)
    return tuple(
        calendar_year_for_horizon_index(modeljaar, h) for h in range(num)
    )
