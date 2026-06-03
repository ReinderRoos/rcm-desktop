"""Welke functies een rapport-hoofdstuk krijgen (slice 57)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rcm_core.models import RCMProject

from rcm_desktop.adapter.report_run_source_service import ReportScenarioRun
from rcm_desktop.adapter.result_filter_service import collect_pbs_subtree_ids
from rcm_desktop.adapter.run_service import RunResult

MetricKind = Literal["nb", "cost"]


@dataclass(frozen=True)
class ReportFunctieChapter:
    functie_id: str
    title: str
    effect_klasse_labels: tuple[str, ...]
    impact_pct: float


@dataclass(frozen=True)
class ReportFunctieSelection:
    nb_chapters: tuple[ReportFunctieChapter, ...]
    cost_chapters: tuple[ReportFunctieChapter, ...]
    excluded_nb_count: int
    excluded_cost_count: int


def _category_match(categorie: str, kind: MetricKind) -> bool:
    cat = categorie.lower()
    if kind == "nb":
        return "beschikbaarheid" in cat
    return "kosten" in cat


def _fm_ids_for_functie(project: RCMProject, functie_id: str, kind: MetricKind) -> frozenset[str]:
    ek_ids = {
        ek.klasse_id
        for ek in project.effect_klassen.values()
        if ek.functie_id == functie_id and _category_match(ek.categorie, kind)
    }
    if not ek_ids:
        return frozenset()
    return frozenset(
        link.fm_id
        for link in project.fm_effect_links.values()
        if link.klasse_id in ek_ids
    )


def _impact_value(
    run: RunResult,
    fm_ids: frozenset[str],
    *,
    kind: MetricKind,
) -> float:
    if not fm_ids:
        return 0.0
    if kind == "cost":
        total = float(run.metrics.total_cost_eur)
        part = sum(
            float(fr.total_cost_eur) for fr in run.fm_core_results if fr.fm_id in fm_ids
        )
        return (part / total * 100.0) if total > 1e-15 else 0.0
    total_hr = float(run.metrics.total_downtime_hr)
    part_hr = sum(
        float(fr.expected_total_downtime_hr) + float(fr.expected_pm_downtime_hr)
        for fr in run.fm_core_results
        if fr.fm_id in fm_ids
    )
    return (part_hr / total_hr * 100.0) if total_hr > 1e-15 else 0.0


def _scope_denominator(
    project: RCMProject,
    run: RunResult,
    scope_id: str | None,
    *,
    kind: MetricKind,
) -> float:
    if scope_id is None or scope_id not in project.pbs_items:
        return 100.0
    subtree = collect_pbs_subtree_ids(project, scope_id)
    if kind == "cost":
        total = sum(float(fr.total_cost_eur) for fr in run.fm_core_results if fr.pbs_id in subtree)
        project_total = float(run.metrics.total_cost_eur)
        return (total / project_total * 100.0) if project_total > 1e-15 else 100.0
    total_hr = sum(
        float(fr.expected_total_downtime_hr) + float(fr.expected_pm_downtime_hr)
        for fr in run.fm_core_results
        if fr.pbs_id in subtree
    )
    project_hr = float(run.metrics.total_downtime_hr)
    return (total_hr / project_hr * 100.0) if project_hr > 1e-15 else 100.0


def _effect_labels(project: RCMProject, functie_id: str, kind: MetricKind) -> tuple[str, ...]:
    labels = [
        ek.omschrijving
        for ek in project.effect_klassen.values()
        if ek.functie_id == functie_id and _category_match(ek.categorie, kind)
    ]
    return tuple(sorted(labels))


def select_report_functies(
    project: RCMProject,
    primary_run: ReportScenarioRun,
    *,
    scope_id: str | None,
    nb_threshold_pct: float,
    cost_threshold_pct: float,
    include_below_threshold: bool,
) -> ReportFunctieSelection:
    run = primary_run.run_result
    scope_scale_nb = _scope_denominator(project, run, scope_id, kind="nb") / 100.0
    scope_scale_cost = _scope_denominator(project, run, scope_id, kind="cost") / 100.0
    nb_thresh = nb_threshold_pct * scope_scale_nb
    cost_thresh = cost_threshold_pct * scope_scale_cost

    nb_candidates: list[ReportFunctieChapter] = []
    cost_candidates: list[ReportFunctieChapter] = []
    excluded_nb = 0
    excluded_cost = 0

    for functie in project.functies.values():
        fm_nb = _fm_ids_for_functie(project, functie.functie_id, "nb")
        if fm_nb:
            impact = _impact_value(run, fm_nb, kind="nb")
            labels = _effect_labels(project, functie.functie_id, "nb")
            chapter = ReportFunctieChapter(
                functie_id=functie.functie_id,
                title=functie.functie_omschrijving,
                effect_klasse_labels=labels,
                impact_pct=impact,
            )
            if impact >= nb_thresh or include_below_threshold:
                nb_candidates.append(chapter)
            else:
                excluded_nb += 1

        labels_cost = _effect_labels(project, functie.functie_id, "cost")
        if labels_cost:
            fm_cost = _fm_ids_for_functie(project, functie.functie_id, "cost")
            impact = _impact_value(run, fm_cost, kind="cost")
            chapter = ReportFunctieChapter(
                functie_id=functie.functie_id,
                title=functie.functie_omschrijving,
                effect_klasse_labels=labels_cost,
                impact_pct=impact,
            )
            if impact >= cost_thresh or include_below_threshold:
                cost_candidates.append(chapter)
            else:
                excluded_cost += 1

    nb_candidates.sort(key=lambda c: c.impact_pct, reverse=True)
    cost_candidates.sort(key=lambda c: c.impact_pct, reverse=True)
    return ReportFunctieSelection(
        nb_chapters=tuple(nb_candidates),
        cost_chapters=tuple(cost_candidates),
        excluded_nb_count=excluded_nb,
        excluded_cost_count=excluded_cost,
    )
