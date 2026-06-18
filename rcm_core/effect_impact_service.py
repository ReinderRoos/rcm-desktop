"""Effectimpact-aggregatie — Qt-vrije deep module (slice 70 issue 03)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from rcm_core.effect_taxonomy import (
    CATEGORIE_BESCHIKBAARHEID,
    CATEGORIE_KOSTEN,
    CATEGORIE_OVERIG,
    CATEGORIE_VEILIGHEID,
)
from rcm_core.lcc_profile import ltap_horizon_bucket_count
from rcm_core.models import FMResult, RCMProject

FunctieScopeKind = Literal["all", "nb", "cost", "veiligheid"]

_HOURS_PER_YEAR = 8760.0

#: Selecteerbare pseudo-effectklasse die de detectievertraging / verborgen
#: niet-beschikbaarheid (+ niet-toegewezen PM) vertegenwoordigt. Samen met de
#: echte availability-effectklassen vormt dit een partitie van de totale NB
#: (zie ADR-0010, CONTEXT.md "Detectie-/verborgen-NB-restpost").
HIDDEN_NB_RESTPOST_ID = "__hidden_nb_restpost__"
HIDDEN_NB_RESTPOST_LABEL = "Detectie-/verborgen niet-beschikbaarheid"


@dataclass(frozen=True)
class EffectNbFilterSet:
    """Multi-select NB-effectklassen; leeg = totale niet-beschikbaarheid (slice 33)."""

    selected_klasse_ids: frozenset[str] = frozenset()

    def is_all(self) -> bool:
        return len(self.selected_klasse_ids) == 0


@dataclass(frozen=True)
class EffectImpactRow:
    klasse_id: str
    label: str
    categorie: str
    aw_effect_type: str
    rf_display: str
    waarde_cm: float
    waarde_pm: float
    waarde_totaal: float
    eenheid: str
    share_pct: float


@dataclass(frozen=True)
class EffectPresentation:
    horizon: str = "lifecycle"
    year_index: int | None = None
    unavailability_display: Literal["hours", "percent"] = "hours"


def collect_fm_ids_for_functie(
    project: RCMProject,
    functie_id: str,
    kind: FunctieScopeKind = "all",
) -> frozenset[str]:
    """SSOT: FM's gekoppeld aan effectklassen van een functie."""
    ek_ids = _effect_klasse_ids_for_functie(project, functie_id, kind)
    if not ek_ids:
        return frozenset()
    return frozenset(
        link.fm_id
        for link in project.fm_effect_links.values()
        if link.klasse_id in ek_ids
    )


def _effect_klasse_ids_for_functie(
    project: RCMProject,
    functie_id: str,
    kind: FunctieScopeKind,
) -> set[str]:
    out: set[str] = set()
    for ek in project.effect_klassen.values():
        if ek.functie_id != functie_id:
            continue
        if kind == "all":
            out.add(ek.klasse_id)
            continue
        cat = ek.categorie.lower()
        if kind == "nb" and CATEGORIE_BESCHIKBAARHEID in cat:
            out.add(ek.klasse_id)
        elif kind == "veiligheid" and CATEGORIE_VEILIGHEID in cat:
            out.add(ek.klasse_id)
        elif kind == "cost" and CATEGORIE_KOSTEN in cat:
            out.add(ek.klasse_id)
    return out


def aggregate(
    project: RCMProject,
    fm_results: dict[str, FMResult] | tuple[FMResult, ...] | list[FMResult],
    *,
    scope_id: str | None = None,
    fm_ids: frozenset[str] | None = None,
    categorie_filter: str | None = None,
    presentation: EffectPresentation | None = None,
) -> tuple[EffectImpactRow, ...]:
    """Aggregeer effectimpact per effectklasse over scope."""
    pres = presentation or EffectPresentation()
    fm_list = _normalize_fm_results(fm_results)
    scoped = _filter_fm_results(project, fm_list, scope_id=scope_id, fm_ids=fm_ids)
    if not scoped:
        return ()

    raw: dict[str, dict[str, float]] = {}
    rf_by_klasse: dict[str, set[float]] = {}
    for fmr in scoped:
        fm = project.faalwijzes.get(fmr.fm_id)
        downtime_hr = float(fm.downtime_per_failure.to_hours()) if fm is not None else 0.0
        fm_cm, fm_pm = _raw_contributions(fmr, pres)
        for klasse_id in set(fm_cm) | set(fm_pm):
            bucket = raw.setdefault(
                klasse_id,
                {"cm_raw": 0.0, "pm_raw": 0.0, "cm_hr": 0.0, "pm_hr": 0.0},
            )
            cm = fm_cm.get(klasse_id, 0.0)
            pm = fm_pm.get(klasse_id, 0.0)
            bucket["cm_raw"] += cm
            bucket["pm_raw"] += pm
            # Bug 3: CM is een telling (incidenten) → vermenigvuldig per FM met
            # díe FM's downtime, niet met de downtime van de eerste FM die de
            # klasse raakt. PM is al in uren (engine: duration × RF × executions).
            bucket["cm_hr"] += cm * downtime_hr
            bucket["pm_hr"] += pm
        for link in project.get_fm_effect_links_for_fm(fmr.fm_id):
            rf_by_klasse.setdefault(link.klasse_id, set()).add(float(link.fractie))
        pm_task_ids = {t.pm_id for t in project.get_pm_tasks_for_fm(fmr.fm_id)}
        for link in project.pm_effect_links.values():
            if link.pm_id in pm_task_ids:
                rf_by_klasse.setdefault(link.klasse_id, set()).add(float(link.fractie))

    rows: list[EffectImpactRow] = []
    for klasse_id, parts in raw.items():
        ek = project.effect_klassen.get(klasse_id)
        categorie = ek.categorie if ek is not None else CATEGORIE_OVERIG
        if categorie_filter and categorie != categorie_filter:
            continue
        cm_val, pm_val, totaal, eenheid = _present_values(
            categorie,
            cm_raw=parts["cm_raw"],
            pm_raw=parts["pm_raw"],
            cm_hr=parts["cm_hr"],
            pm_hr=parts["pm_hr"],
        )
        label = ek.omschrijving if ek is not None else klasse_id
        aw_type = ek.aw_effect_type if ek is not None else ""
        rf_display = _format_rf_values(rf_by_klasse.get(klasse_id, set()))
        rows.append(
            EffectImpactRow(
                klasse_id=klasse_id,
                label=label,
                categorie=categorie,
                aw_effect_type=aw_type,
                rf_display=rf_display,
                waarde_cm=cm_val,
                waarde_pm=pm_val,
                waarde_totaal=totaal,
                eenheid=eenheid,
                share_pct=0.0,
            )
        )

    rows.sort(key=lambda r: r.waarde_totaal, reverse=True)
    total = sum(r.waarde_totaal for r in rows)
    if total > 1e-15:
        rows = [
            replace(r, share_pct=(r.waarde_totaal / total) * 100.0)
            for r in rows
        ]
    return tuple(rows)


def _normalize_fm_results(
    fm_results: dict[str, FMResult] | tuple[FMResult, ...] | list[FMResult],
) -> list[FMResult]:
    if isinstance(fm_results, dict):
        return list(fm_results.values())
    return list(fm_results)


def _filter_fm_results(
    project: RCMProject,
    fm_results: list[FMResult],
    *,
    scope_id: str | None,
    fm_ids: frozenset[str] | None,
) -> list[FMResult]:
    scoped = fm_results
    if scope_id is not None and scope_id in project.pbs_items:
        subtree = _collect_pbs_subtree_ids(project, scope_id)
        scoped = [fmr for fmr in scoped if fmr.pbs_id in subtree]
    if fm_ids is not None:
        scoped = [fmr for fmr in scoped if fmr.fm_id in fm_ids]
    return scoped


def _collect_pbs_subtree_ids(project: RCMProject, scope_id: str) -> frozenset[str]:
    children: dict[str, list[str]] = {}
    for pid, item in project.pbs_items.items():
        if item.parent_pbs_id is None:
            continue
        if item.parent_pbs_id not in project.pbs_items:
            continue
        children.setdefault(item.parent_pbs_id, []).append(pid)

    collected: set[str] = set()
    stack: list[str] = [scope_id]
    while stack:
        current = stack.pop()
        if current in collected:
            continue
        collected.add(current)
        stack.extend(children.get(current, ()))
    return frozenset(collected)


def _raw_contributions(
    fmr: FMResult,
    presentation: EffectPresentation,
) -> tuple[dict[str, float], dict[str, float]]:
    if presentation.horizon == "lifecycle":
        fm = dict(fmr.fm_effect_bijdragen)
        pm = dict(fmr.pm_effect_bijdragen)
        if not fm and not pm and fmr.effect_bijdragen:
            fm = dict(fmr.effect_bijdragen)
        return fm, pm

    idx = presentation.year_index
    if idx is None:
        return {}, {}

    fm: dict[str, float] = {}
    pm: dict[str, float] = {}
    for klasse_id, series in fmr.fm_effect_bijdragen_per_jaar.items():
        if 0 <= idx < len(series):
            fm[klasse_id] = float(series[idx])
    for klasse_id, series in fmr.pm_effect_bijdragen_per_jaar.items():
        if 0 <= idx < len(series):
            pm[klasse_id] = float(series[idx])
    if not fm and not pm and fmr.effect_bijdragen_per_jaar:
        for klasse_id, series in fmr.effect_bijdragen_per_jaar.items():
            if 0 <= idx < len(series):
                fm[klasse_id] = float(series[idx])
    return fm, pm


def _present_values(
    categorie: str,
    *,
    cm_raw: float,
    pm_raw: float,
    cm_hr: float,
    pm_hr: float,
) -> tuple[float, float, float, str]:
    cat = categorie.lower()
    if CATEGORIE_BESCHIKBAARHEID in cat:
        # CM-uren = Σ_FM (telling × downtime van díe FM); PM is al in uren.
        return cm_hr, pm_hr, cm_hr + pm_hr, "uren"
    if CATEGORIE_VEILIGHEID in cat:
        return cm_raw, pm_raw, cm_raw, "incidenten"
    if CATEGORIE_KOSTEN in cat:
        return cm_raw, pm_raw, cm_raw + pm_raw, "incidenten"
    return cm_raw, pm_raw, cm_raw + pm_raw, "incidenten"


def _format_rf_values(values: set[float]) -> str:
    if not values:
        return "—"
    parts = sorted(values)
    return " / ".join(f"{v:g}".replace(".", ",") for v in parts)


def horizon_index_for_calendar_year(project: RCMProject, calendar_year: int) -> int | None:
    modeljaar = int(project.config.modeljaar)
    idx = int(calendar_year) - modeljaar
    num = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    if 0 <= idx < num:
        return idx
    return None


def list_nb_effect_klassen(project: RCMProject) -> tuple[tuple[str, str], ...]:
    """Effectklassen met categorie beschikbaarheid (geen VGM/veiligheid)."""
    rows: list[tuple[str, str]] = []
    for ek in project.effect_klassen.values():
        if CATEGORIE_BESCHIKBAARHEID not in ek.categorie.lower():
            continue
        rows.append((ek.klasse_id, ek.omschrijving))
    rows.sort(key=lambda t: t[1].lower())
    # Restpost als laatste, selecteerbare post → echte partitie van de totale NB.
    rows.append((HIDDEN_NB_RESTPOST_ID, HIDDEN_NB_RESTPOST_LABEL))
    return tuple(rows)


def nb_scalar_for_fm(
    project: RCMProject,
    fmr: FMResult,
    *,
    nb_filter: EffectNbFilterSet | None = None,
    presentation: EffectPresentation | None = None,
) -> float:
    """NB-scalar per FM als reductie van de NB-bucketreeks (per FM).

    Lege filter = totale NB; anders de som van de geselecteerde posten
    (effectklassen + optioneel de Detectie-/verborgen-NB-restpost), per bucket
    geclamped op het totaal. De scalar is per constructie een reductie van de
    curve die ``nb_yearly_series`` tekent (ADR-0010).
    """
    pres = presentation or EffectPresentation()
    filt = nb_filter or EffectNbFilterSet()
    num = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    if num <= 0:
        return 0.0
    buckets = _nb_bucket_series_for_fm(project, fmr, filt, num)
    return _reduce_bucket_series(project, buckets, pres)


def nb_yearly_series(
    project: RCMProject,
    fm_results: dict[str, FMResult] | tuple[FMResult, ...] | list[FMResult],
    *,
    nb_filter: EffectNbFilterSet | None = None,
    scope_id: str | None = None,
    fm_ids: frozenset[str] | None = None,
    presentation: EffectPresentation | None = None,
) -> list[float]:
    """Gepresenteerde NB per horizonbucket over scope (uren of % via presentation).

    Som over FM's van de NB-bucketreeks (per FM); dezelfde spine waaruit
    ``nb_scalar_for_fm`` reduceert.
    """
    pres = presentation or EffectPresentation()
    filt = nb_filter or EffectNbFilterSet()
    fm_list = _filter_fm_results(
        project,
        _normalize_fm_results(fm_results),
        scope_id=scope_id,
        fm_ids=fm_ids,
    )
    num = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    if num <= 0:
        return []
    totals = [0.0] * num
    for fmr in fm_list:
        buckets = _nb_bucket_series_for_fm(project, fmr, filt, num)
        for h in range(num):
            totals[h] += buckets[h]
    return _present_nb_bucket_series(project, totals, pres)


def _nb_bucket_series_for_fm(
    project: RCMProject,
    fmr: FMResult,
    filt: EffectNbFilterSet,
    num: int,
) -> list[float]:
    """De NB-bucketreeks (per FM) in uren voor één filterselectie.

    De enige bron-van-waarheid: lege filter = totaal; anders de som van de
    geselecteerde posten, per bucket geclamped op het totaal (veiligheids-clamp
    voor zeldzame RF-overlap, ADR-0010). De restpost = totaal − reële
    availability-klassen, zodat de selecteerbare posten een echte partitie van
    het totaal vormen.
    """
    total = _total_nb_hours_per_bucket(project, fmr, num)
    if filt.is_all():
        return total
    out = [0.0] * num
    for kid in filt.selected_klasse_ids:
        if kid == HIDDEN_NB_RESTPOST_ID:
            real = _real_availability_buckets_for_fm(project, fmr, num)
            for h in range(num):
                out[h] += max(0.0, total[h] - real[h])
        else:
            series = effect_yearly_series(project, (fmr,), kid)
            for h in range(num):
                out[h] += float(series[h]) if h < len(series) else 0.0
    return [min(out[h], total[h]) for h in range(num)]


def _real_availability_buckets_for_fm(
    project: RCMProject,
    fmr: FMResult,
    num: int,
) -> list[float]:
    """Som van de reële availability-effectklassen (excl. restpost) per bucket."""
    out = [0.0] * num
    kids = set(fmr.fm_effect_bijdragen_per_jaar) | set(fmr.pm_effect_bijdragen_per_jaar)
    for kid in kids:
        ek = project.effect_klassen.get(kid)
        if ek is None or CATEGORIE_BESCHIKBAARHEID not in ek.categorie.lower():
            continue
        series = effect_yearly_series(project, (fmr,), kid)
        for h in range(num):
            out[h] += float(series[h]) if h < len(series) else 0.0
    return out


def _reduce_bucket_series(
    project: RCMProject,
    buckets: list[float],
    presentation: EffectPresentation,
) -> float:
    """Reduceer een uren-bucketreeks tot één scalar volgens de presentation."""
    if not buckets:
        return 0.0
    if presentation.horizon == "lifecycle":
        hours = float(sum(buckets))
        if presentation.unavailability_display == "percent":
            lifecycle_hours = float(project.config.lifecycle_years) * _HOURS_PER_YEAR
            if lifecycle_hours <= 0.0:
                return 0.0
            return (hours / lifecycle_hours) * 100.0
        return hours
    if presentation.year_index is not None and 0 <= presentation.year_index < len(buckets):
        hr = float(buckets[presentation.year_index])
    else:
        hr = float(sum(buckets)) / len(buckets)
    if presentation.unavailability_display == "percent":
        return (hr / _HOURS_PER_YEAR) * 100.0
    return hr


def _total_nb_hours_per_bucket(
    project: RCMProject,
    fmr: FMResult,
    num: int,
) -> list[float]:
    hp = fmr.horizon_profile
    if hp is not None and len(hp.cor_downtime_hr) >= num:
        cm = list(hp.cor_downtime_hr[:num])
        hidden = list(hp.hidden_nb_hr[:num]) if hp.hidden_nb_hr else [0.0] * num
        while len(hidden) < num:
            hidden.append(0.0)
        combined = [float(cm[i]) + float(hidden[i]) for i in range(num)]
        target_cm = float(fmr.expected_total_downtime_hr)
        cm_sum = float(sum(combined))
        if cm_sum > 0.0 and not abs(cm_sum - target_cm) < 1e-4:
            scale = target_cm / cm_sum
            combined = [v * scale for v in combined]
        pm_per = _pm_downtime_per_bucket(project, fmr, num)
        return [combined[i] + pm_per[i] for i in range(num)]

    target = float(fmr.expected_total_downtime_hr) + float(fmr.expected_pm_downtime_hr)
    if num <= 0:
        return []
    per = target / num
    return [per] * num


def _pm_downtime_per_bucket(project: RCMProject, fmr: FMResult, num: int) -> list[float]:
    target_pm = float(fmr.expected_pm_downtime_hr)
    if target_pm <= 0.0:
        return [0.0] * num
    pm_series: list[float] = []
    for klasse_id, series in fmr.pm_effect_bijdragen_per_jaar.items():
        ek = project.effect_klassen.get(klasse_id)
        if ek is None or CATEGORIE_BESCHIKBAARHEID not in ek.categorie.lower():
            continue
        while len(series) < num:
            series = list(series) + [0.0]
        for h in range(num):
            if h >= len(pm_series):
                pm_series.extend([0.0] * (h + 1 - len(pm_series)))
            pm_series[h] += float(series[h])
    if pm_series and sum(pm_series) > 0:
        scale = target_pm / sum(pm_series)
        return [v * scale for v in pm_series[:num]] + [0.0] * max(0, num - len(pm_series))
    per = target_pm / num
    return [per] * num


def _present_nb_bucket_series(
    project: RCMProject,
    hours_buckets: list[float],
    presentation: EffectPresentation,
) -> list[float]:
    if presentation.unavailability_display != "percent":
        return hours_buckets
    return [(hr / _HOURS_PER_YEAR) * 100.0 for hr in hours_buckets]


def effect_yearly_series(
    project: RCMProject,
    fm_results: dict[str, FMResult] | tuple[FMResult, ...] | list[FMResult],
    klasse_id: str,
    *,
    scope_id: str | None = None,
    fm_ids: frozenset[str] | None = None,
) -> list[float]:
    """Gepresenteerde effectimpact per horizonbucket (issue 09)."""
    fm_list = _filter_fm_results(
        project,
        _normalize_fm_results(fm_results),
        scope_id=scope_id,
        fm_ids=fm_ids,
    )
    num = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    if num <= 0:
        return []

    totals = [0.0] * num
    for fmr in fm_list:
        fm = project.faalwijzes.get(fmr.fm_id)
        downtime_hr = float(fm.downtime_per_failure.to_hours()) if fm is not None else 0.0
        ek = project.effect_klassen.get(klasse_id)
        categorie = ek.categorie if ek is not None else CATEGORIE_OVERIG
        fm_series = fmr.fm_effect_bijdragen_per_jaar.get(klasse_id, [0.0] * num)
        pm_series = fmr.pm_effect_bijdragen_per_jaar.get(klasse_id, [0.0] * num)
        while len(fm_series) < num:
            fm_series = list(fm_series) + [0.0]
        while len(pm_series) < num:
            pm_series = list(pm_series) + [0.0]
        for h in range(num):
            cm_raw = float(fm_series[h])
            pm_raw = float(pm_series[h])
            cm_val, pm_val, totaal, _ = _present_values(
                categorie,
                cm_raw=cm_raw,
                pm_raw=pm_raw,
                cm_hr=cm_raw * downtime_hr,
                pm_hr=pm_raw,
            )
            totals[h] += totaal
    return totals
