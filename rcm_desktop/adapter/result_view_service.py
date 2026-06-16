from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

from rcm_core.effect_impact_service import (
    EffectNbFilterSet,
    EffectPresentation,
    nb_scalar_for_fm,
)
from rcm_core.models import FMResult, PBSResult, RCMProject

if False:  # typing-only import cycle guard
    from rcm_desktop.adapter.results_workspace_state import ContributionPresentation

#: FM-detail-tabel rekent in levensduur-uren (consistent met de kolomsemantiek).
_FM_DETAIL_NB_PRESENTATION = EffectPresentation(
    horizon="lifecycle", unavailability_display="hours"
)


@dataclass(frozen=True)
class FMRfTooltipEntry:
    klasse_id: str
    effect_omschrijving: str
    fractie: float


@dataclass(frozen=True)
class FMResultRow:
    fm_id: str
    faalwijze_omschrijving: str
    pbs_id: str
    bouwdeel_naam: str
    expected_failures: float
    expected_total_downtime_hr: float
    total_cost_eur: float
    is_nmf: bool = False
    rf: float = 0.0
    rf_tooltip_entries: tuple[FMRfTooltipEntry, ...] = ()


@dataclass(frozen=True)
class PBSResultRow:
    pbs_id: str
    bouwdeel_naam: str
    parent_pbs_id: str | None
    level: int
    sort_path: tuple[str, ...]
    expected_failures_self: float
    total_downtime_hr_self: float
    total_cost_eur_self: float
    expected_failures_total: float
    total_downtime_hr_total: float
    total_cost_eur_total: float
    unavailability_pct_total: float
    effect_bijdragen: tuple[tuple[str, float], ...] = ()


def build_rows(project: RCMProject, fm_results: list[FMResult]) -> list[FMResultRow]:
    rows: list[FMResultRow] = []
    for fm_result in fm_results:
        fm = project.faalwijzes.get(fm_result.fm_id)
        pbs_item = project.pbs_items.get(fm_result.pbs_id)
        is_nmf = bool(fm is not None and not fm.is_evident)
        rows.append(
            FMResultRow(
                fm_id=fm_result.fm_id,
                faalwijze_omschrijving=fm.faalwijze_omschrijving if fm is not None else "",
                pbs_id=fm_result.pbs_id,
                bouwdeel_naam=pbs_item.bouwdeel_naam if pbs_item is not None else "",
                expected_failures=fm_result.expected_failures,
                expected_total_downtime_hr=fm_result.expected_total_downtime_hr,
                total_cost_eur=fm_result.total_cost_eur,
                is_nmf=is_nmf,
            )
        )
    return rows


def _rf_link_entries(
    project: RCMProject,
    fm_id: str,
) -> tuple[FMRfTooltipEntry, ...]:
    entries: list[FMRfTooltipEntry] = []
    for link in project.get_fm_effect_links_for_fm(fm_id):
        ek = project.effect_klassen.get(link.klasse_id)
        omsch = ek.omschrijving if ek is not None else link.klasse_id
        entries.append(
            FMRfTooltipEntry(
                klasse_id=link.klasse_id,
                effect_omschrijving=omsch,
                fractie=float(link.fractie),
            )
        )
    entries.sort(key=lambda e: (-e.fractie, e.klasse_id))
    return tuple(entries)


def _resolve_rf_for_fm(
    project: RCMProject,
    fm_id: str,
    nb_filter: EffectNbFilterSet,
) -> tuple[float, tuple[FMRfTooltipEntry, ...]]:
    all_entries = _rf_link_entries(project, fm_id)
    if not all_entries:
        return 0.0, ()

    selected = nb_filter.selected_klasse_ids
    if len(selected) == 1:
        klasse_id = next(iter(selected))
        for entry in all_entries:
            if entry.klasse_id == klasse_id:
                return entry.fractie, ()
        return 0.0, ()

    if selected:
        scoped = tuple(e for e in all_entries if e.klasse_id in selected)
    else:
        scoped = all_entries
    if not scoped:
        return 0.0, ()
    return scoped[0].fractie, scoped


def enrich_fm_rows_with_nmf_rf(
    project: RCMProject,
    *,
    out: Sequence[FMResultRow],
    nb_filter: EffectNbFilterSet | None,
) -> tuple[FMResultRow, ...]:
    filt = nb_filter or EffectNbFilterSet()
    enriched: list[FMResultRow] = []
    for row in out:
        rf, tooltip = _resolve_rf_for_fm(project, row.fm_id, filt)
        enriched.append(replace(row, rf=rf, rf_tooltip_entries=tooltip))
    return tuple(enriched)


def apply_presentation_scale_to_fm_rows(
    project: RCMProject,
    fm_results: Sequence[FMResult],
    rows: Sequence[FMResultRow],
    *,
    presentation: "ContributionPresentation",
    nb_filter: EffectNbFilterSet | None,
) -> tuple[FMResultRow, ...]:
    from rcm_desktop.adapter.contribution_horizon_value_service import (
        contribution_value_for_fm,
        effect_presentation_for_contribution,
        kosten_scalar_for_fm,
    )
    from rcm_desktop.adapter.results_workspace_state import METRIC_FAALMOMENTEN

    filt = nb_filter or EffectNbFilterSet()
    effect_pres = effect_presentation_for_contribution(project, presentation)
    fmr_by_id = {fmr.fm_id: fmr for fmr in fm_results}
    out: list[FMResultRow] = []
    for row in rows:
        fmr = fmr_by_id.get(row.fm_id)
        if fmr is None:
            out.append(row)
            continue
        failures = contribution_value_for_fm(
            project, fmr, metric=METRIC_FAALMOMENTEN, presentation=presentation
        )
        downtime = nb_scalar_for_fm(
            project, fmr, nb_filter=filt, presentation=effect_pres
        )
        cost = kosten_scalar_for_fm(project, fmr, presentation)
        out.append(
            replace(
                row,
                expected_failures=failures,
                expected_total_downtime_hr=downtime,
                total_cost_eur=cost,
            )
        )
    return tuple(out)


def apply_presentation_scale_to_mc_rows(
    project: RCMProject,
    mc: "MCRunResult",
    rows: "Sequence[FMMCResultRow]",
    *,
    presentation: "ContributionPresentation",
    nb_filter: EffectNbFilterSet | None,
) -> "tuple[FMMCResultRow, ...]":
    """Scale MC P50 band rows to match ``ContributionPresentation`` (slice 101)."""
    from rcm_core.simulation_engine import MetricBand

    from rcm_desktop.adapter.contribution_horizon_value_service import (
        contribution_value_for_fm,
        effect_presentation_for_contribution,
        kosten_scalar_for_fm,
    )
    from rcm_desktop.adapter.results_workspace_state import METRIC_FAALMOMENTEN
    from rcm_desktop.adapter.simulation_engine_service import (
        FMMCResultRow,
        fm_results_from_mc_p50,
    )

    filt = nb_filter or EffectNbFilterSet()
    effect_pres = effect_presentation_for_contribution(project, presentation)
    lifecycle_effect = effect_presentation_for_contribution(
        project, replace(presentation, horizon="lifecycle")
    )
    fmr_by_id = {fmr.fm_id: fmr for fmr in fm_results_from_mc_p50(project, mc)}

    def _scale_band(band: MetricBand, display: float, lifecycle: float) -> MetricBand:
        if lifecycle <= 0.0:
            return MetricBand(p10=0.0, p50=display, p90=0.0)
        factor = display / lifecycle
        return MetricBand(
            p10=band.p10 * factor,
            p50=display,
            p90=band.p90 * factor,
        )

    out: list[FMMCResultRow] = []
    for row in rows:
        fmr = fmr_by_id.get(row.fm_id)
        if fmr is None:
            out.append(row)
            continue
        display_failures = contribution_value_for_fm(
            project, fmr, metric=METRIC_FAALMOMENTEN, presentation=presentation
        )
        display_downtime = nb_scalar_for_fm(
            project, fmr, nb_filter=filt, presentation=effect_pres
        )
        display_cost = kosten_scalar_for_fm(project, fmr, presentation)
        lifecycle_downtime = nb_scalar_for_fm(
            project, fmr, nb_filter=filt, presentation=lifecycle_effect
        )
        out.append(
            replace(
                row,
                failures_band=_scale_band(
                    row.failures_band, display_failures, float(fmr.expected_failures)
                ),
                downtime_band=_scale_band(
                    row.downtime_band, display_downtime, lifecycle_downtime
                ),
                cost_band=_scale_band(
                    row.cost_band, display_cost, float(fmr.total_cost_eur)
                ),
            )
        )
    return tuple(out)


def apply_nb_filter_to_fm_rows(
    project: RCMProject,
    fm_results: Sequence[FMResult],
    rows: Sequence[FMResultRow],
    nb_filter: EffectNbFilterSet | None,
) -> tuple[FMResultRow, ...]:
    """Vervang de downtime-kolom door de NB-gefilterde waarde (render-tijd).

    Lege filter (``is_all()``) short-circuit: de rijen blijven exact gelijk aan
    ``build_rows`` (geen recompute). Bij een gevulde filter wordt
    ``expected_total_downtime_hr`` per rij vervangen door
    ``nb_scalar_for_fm(...)`` (levensduur/uren) — dezelfde NB-bucketreeks-spine
    als Top 10/Tijdsplot (ADR-0010). Andere velden (faalmomenten, kosten)
    blijven ongewijzigd; de filter raakt alleen NB.
    """
    filt = nb_filter or EffectNbFilterSet()
    if filt.is_all():
        return tuple(rows)
    fmr_by_id = {fmr.fm_id: fmr for fmr in fm_results}
    out: list[FMResultRow] = []
    for row in rows:
        fmr = fmr_by_id.get(row.fm_id)
        if fmr is None:
            out.append(row)
            continue
        filtered = nb_scalar_for_fm(
            project,
            fmr,
            nb_filter=filt,
            presentation=_FM_DETAIL_NB_PRESENTATION,
        )
        out.append(replace(row, expected_total_downtime_hr=filtered))
    return tuple(out)


def build_pbs_rows(project: RCMProject, pbs_results: dict[str, PBSResult]) -> list[PBSResultRow]:
    if not pbs_results:
        return []

    children: dict[str, list[str]] = {}
    for pbs_id, item in project.pbs_items.items():
        parent_id = item.parent_pbs_id if item.parent_pbs_id in project.pbs_items else None
        children.setdefault(parent_id or "", []).append(pbs_id)
    for ids in children.values():
        ids.sort(key=lambda pid: (project.pbs_items[pid].volgorde, pid))

    lifecycle_hours = float(project.config.lifecycle_years) * 8760.0
    def _self_values(pbs_id: str) -> tuple[float, float, float]:
        result = pbs_results.get(pbs_id)
        if result is None:
            return 0.0, 0.0, 0.0
        return result.total_expected_failures, result.total_downtime_hr, result.total_cost_eur

    def _totals(pbs_id: str, in_path: set[str]) -> tuple[float, float, float]:
        expected_failures_self, total_downtime_hr_self, total_cost_eur_self = _self_values(pbs_id)
        expected_failures_total = expected_failures_self
        total_downtime_hr_total = total_downtime_hr_self
        total_cost_eur_total = total_cost_eur_self
        next_path = set(in_path)
        next_path.add(pbs_id)
        for child_id in children.get(pbs_id, []):
            if child_id in next_path:
                continue
            child_failures, child_downtime, child_cost = _totals(child_id, next_path)
            expected_failures_total += child_failures
            total_downtime_hr_total += child_downtime
            total_cost_eur_total += child_cost
        return expected_failures_total, total_downtime_hr_total, total_cost_eur_total

    totals_by_id: dict[str, tuple[float, float, float]] = {
        pbs_id: _totals(pbs_id, set()) for pbs_id in project.pbs_items
    }

    emitted: set[str] = set()
    rows: list[PBSResultRow] = []

    def _walk(pbs_id: str, level: int, path: tuple[str, ...], in_path: set[str]) -> None:
        if pbs_id in emitted:
            return

        emitted.add(pbs_id)
        expected_failures_self, total_downtime_hr_self, total_cost_eur_self = _self_values(pbs_id)
        expected_failures_total, total_downtime_hr_total, total_cost_eur_total = totals_by_id[pbs_id]

        next_path = path + (pbs_id,)

        pbs_result = pbs_results.get(pbs_id)
        effect_bijdragen: tuple[tuple[str, float], ...] = ()
        if pbs_result is not None and pbs_result.effect_bijdragen:
            effect_bijdragen = tuple(
                sorted((str(k), float(v)) for k, v in pbs_result.effect_bijdragen.items())
            )

        row = PBSResultRow(
            pbs_id=pbs_id,
            bouwdeel_naam=project.pbs_items[pbs_id].bouwdeel_naam,
            parent_pbs_id=project.pbs_items[pbs_id].parent_pbs_id,
            level=level,
            sort_path=next_path,
            expected_failures_self=expected_failures_self,
            total_downtime_hr_self=total_downtime_hr_self,
            total_cost_eur_self=total_cost_eur_self,
            expected_failures_total=expected_failures_total,
            total_downtime_hr_total=total_downtime_hr_total,
            total_cost_eur_total=total_cost_eur_total,
            unavailability_pct_total=(
                0.0 if lifecycle_hours <= 0.0 else (total_downtime_hr_total / lifecycle_hours) * 100.0
            ),
            effect_bijdragen=effect_bijdragen,
        )
        rows.append(row)

        next_in_path = set(in_path)
        next_in_path.add(pbs_id)
        for child_id in children.get(pbs_id, []):
            if child_id in next_in_path:
                continue
            _walk(child_id, level + 1, next_path, next_in_path)

    root_ids = children.get("", [])
    for root_id in root_ids:
        if root_id in emitted:
            continue
        _walk(root_id, 0, tuple(), set())

    for remaining_id in sorted(project.pbs_items):
        if remaining_id in emitted:
            continue
        _walk(remaining_id, 0, tuple(), set())

    return rows


@dataclass(frozen=True)
class PBSTreeNode:
    pbs_id: str
    row: PBSResultRow
    children: tuple["PBSTreeNode", ...] = ()


def build_pbs_tree(rows: list[PBSResultRow]) -> tuple[PBSTreeNode, ...]:
    """Bouw PBS-hiërarchie uit rijen; eerste rij per `pbs_id` wint."""
    if not rows:
        return ()

    by_id: dict[str, PBSResultRow] = {}
    for row in rows:
        by_id.setdefault(row.pbs_id, row)

    children_map: dict[str | None, list[str]] = {}
    for pbs_id, row in by_id.items():
        parent = row.parent_pbs_id
        if parent is None or parent not in by_id:
            parent_key: str | None = None
        else:
            parent_key = parent
        children_map.setdefault(parent_key, []).append(pbs_id)
    for child_ids in children_map.values():
        child_ids.sort()

    def make_node(pbs_id: str) -> PBSTreeNode:
        child_ids = children_map.get(pbs_id, [])
        return PBSTreeNode(
            pbs_id=pbs_id,
            row=by_id[pbs_id],
            children=tuple(make_node(cid) for cid in child_ids),
        )

    root_ids = children_map.get(None, [])
    root_ids.sort()
    return tuple(make_node(rid) for rid in root_ids)


def build_pbs_structure_tree(project: RCMProject) -> tuple[PBSTreeNode, ...]:
    """PBS-structuur vóór run: nul-aggregaten, bouwdeel uit `PBSItem`."""
    if not project.pbs_items:
        return ()

    children: dict[str | None, list[str]] = {}
    for pbs_id, item in project.pbs_items.items():
        parent = item.parent_pbs_id
        if parent is None or parent not in project.pbs_items:
            parent_key: str | None = None
        else:
            parent_key = parent
        children.setdefault(parent_key, []).append(pbs_id)
    for child_ids in children.values():
        child_ids.sort(key=lambda pid: (project.pbs_items[pid].volgorde, pid))

    emitted: set[str] = set()
    rows: list[PBSResultRow] = []

    def _walk(pbs_id: str, level: int, path: tuple[str, ...], in_path: set[str]) -> None:
        if pbs_id in emitted:
            return
        emitted.add(pbs_id)
        item = project.pbs_items[pbs_id]
        parent_id = item.parent_pbs_id
        if parent_id not in project.pbs_items:
            parent_id = None
        next_path = path + (pbs_id,)
        rows.append(
            PBSResultRow(
                pbs_id=pbs_id,
                bouwdeel_naam=item.bouwdeel_naam,
                parent_pbs_id=parent_id,
                level=level,
                sort_path=next_path,
                expected_failures_self=0.0,
                total_downtime_hr_self=0.0,
                total_cost_eur_self=0.0,
                expected_failures_total=0.0,
                total_downtime_hr_total=0.0,
                total_cost_eur_total=0.0,
                unavailability_pct_total=0.0,
            )
        )
        next_in_path = set(in_path)
        next_in_path.add(pbs_id)
        for child_id in children.get(pbs_id, ()):
            if child_id in next_in_path:
                continue
            _walk(child_id, level + 1, next_path, next_in_path)

    for root_id in children.get(None, ()):
        if root_id not in emitted:
            _walk(root_id, 0, tuple(), set())
    for remaining_id in sorted(project.pbs_items):
        if remaining_id not in emitted:
            _walk(remaining_id, 0, tuple(), set())

    return build_pbs_tree(rows)
