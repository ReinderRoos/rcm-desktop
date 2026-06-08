"""Pure helpers voor LCC correctief jaarprofiel vorm (slice 42 D1/D2)."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from rcm_core.lcc_profile import build_cor_eur_per_bucket
from rcm_core.models import FMResult, RCMProject


def coefficient_of_variation(values: Sequence[float]) -> float:
    """Populatie-CV van een bucket-reeks; 0 als gemiddelde nul is."""
    if not values:
        return 0.0
    mean = sum(float(v) for v in values) / len(values)
    if mean == 0.0:
        return 0.0
    variance = sum((float(v) - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance) / mean


def max_mean_ratio(values: Sequence[float]) -> float:
    """max(bucket) / mean(bucket); 0 als gemiddelde nul is."""
    if not values:
        return 0.0
    mean = sum(float(v) for v in values) / len(values)
    if mean == 0.0:
        return 0.0
    return max(float(v) for v in values) / mean


def peak_bucket_index(values: Sequence[float]) -> int:
    """Index van het hoogste bucket-element."""
    if not values:
        return 0
    return max(range(len(values)), key=lambda i: float(values[i]))


def _fm_cm_total(fmr: FMResult) -> float:
    hp = fmr.horizon_profile
    if hp is not None and hp.cor_eur:
        return float(sum(hp.cor_eur))
    return float(fmr.expected_cm_cost_eur)


def aging_cm_share(project: RCMProject, fm_results: Sequence[FMResult]) -> float:
    """Aandeel correctief EUR uit aging-faalwijzen t.o.v. portfolio-totaal."""
    total = sum(_fm_cm_total(r) for r in fm_results)
    if total == 0.0:
        return 0.0
    aging = 0.0
    for result in fm_results:
        fm = project.faalwijzes.get(result.fm_id)
        if fm is not None and fm.failure_type.value == "aging":
            aging += _fm_cm_total(result)
    return aging / total


@dataclass(frozen=True)
class LCCCmYearShape:
    buckets: tuple[float, ...]
    cv: float
    max_mean_ratio: float
    aging_cm_share: float
    used_legacy: bool
    reconciles: bool


def characterize_cm_year_shape(
    project: RCMProject,
    fm_results: Mapping[str, FMResult] | Sequence[FMResult],
    *,
    build: Callable[..., tuple[list[float], bool]] = build_cor_eur_per_bucket,
) -> LCCCmYearShape:
    """Characteriseer geaggregeerd LCC-CM-jaarprofiel (DS-4b + vormmetrics)."""
    if isinstance(fm_results, Mapping):
        results = list(fm_results.values())
    else:
        results = list(fm_results)
    buckets, used_legacy = build(project, results)
    target = sum(float(r.expected_cm_cost_eur) for r in results)
    got = float(sum(buckets))
    if got > 0.0 and not math.isclose(got, target, rel_tol=0, abs_tol=1e-4):
        scale = target / got
        buckets = [float(b) * scale for b in buckets]
    bucket_tuple = tuple(float(b) for b in buckets)
    reconciles = math.isclose(sum(bucket_tuple), target, rel_tol=0, abs_tol=1e-4)
    return LCCCmYearShape(
        buckets=bucket_tuple,
        cv=coefficient_of_variation(bucket_tuple),
        max_mean_ratio=max_mean_ratio(bucket_tuple),
        aging_cm_share=aging_cm_share(project, results),
        used_legacy=used_legacy,
        reconciles=reconciles,
    )
