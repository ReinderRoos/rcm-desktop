"""
engine.py — Analytische rekenkern voor het RCM-model.

Stateless functies: alle staat wordt doorgegeven via dataklassen.
Geen I/O, geen UI-objecten.
"""
from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from typing import Optional

from rcm_core.config import RCMConfig
from rcm_core.models import (
    Faalwijze, FMEffectLink, FMResult, PBSItem, PBSResult,
    PMEffectLink, PMTask, RCMProject, TaskGroup, TaskType,
)
from rcm_core.units import HOURS_PER_YEAR
from rcm_core.distributions import (
    build_rev_schedule,
    effective_age_after_repair,
    expected_aging_lifecycle_faalmomenten_ssot,
    expected_failures_lifecycle,
    p_failure_by_age,
)
from rcm_core.lcc_profile import build_fm_horizon_profile, compute_fm_faalmomenten_per_bucket
from rcm_core.lifecycle_horizon import effective_lifecycle_end_age


# ---------------------------------------------------------------------------
# Detectievertraging voor niet-merkbaar falen
# ---------------------------------------------------------------------------

def compute_detection_delay_hr(fm: Faalwijze, pm_tasks: list[PMTask]) -> float:
    """Gemiddelde detectievertraging voor niet-merkbaar falen (in uren).

    Als falen niet merkbaar is, wordt het pas ontdekt bij de eerstvolgende
    IN- of TST-taak. Gemiddelde vertraging = helft van het kortste interval.

    Als er geen IN/TST-taak is: vertraging onbekend → inf (signaleert onvolledige modellering).
    """
    if fm.is_evident:
        return 0.0
    intervals_hr = [
        t.interval_jaar * HOURS_PER_YEAR
        for t in pm_tasks
        if t.taak_type in (TaskType.IN, TaskType.TST)
    ]
    if not intervals_hr:
        return float("inf")
    return min(intervals_hr) / 2.0


# ---------------------------------------------------------------------------
# PM-kosten en PM-downtime (inclusief taakgroepdeduplicatie)
# ---------------------------------------------------------------------------

def compute_pm_totals(
    pm_tasks: list[PMTask],
    task_groups: dict[str, TaskGroup],
    lifecycle_years: float,
    counted_group_ids: Optional[set[str]] = None,
    pm_effect_links: Optional[list[PMEffectLink]] = None,
) -> tuple[float, float, dict[str, float]]:
    """Retourneert (pm_cost_eur, pm_downtime_hr, pm_effect_bijdragen) over de gehele lifecycle.

    counted_group_ids: set van group_id's waarvan de kosten al zijn meegerekend
    (voor andere FM's in dezelfde groep). Geef een gedeelde set door vanuit
    compute_pbs_results om groepskosten maar éénmalig te tellen.

    pm_effect_bijdragen: klasse_id → totale uren degradatie over lifecycle per effectklasse.
    """
    if counted_group_ids is None:
        counted_group_ids = set()
    if pm_effect_links is None:
        pm_effect_links = []

    total_cost = 0.0
    total_downtime_hr = 0.0
    pm_effect_bijdragen: dict[str, float] = {}

    # Maak snelle lookup: pm_id → lijst van PMEffectLink
    links_by_pm: dict[str, list[PMEffectLink]] = {}
    for link in pm_effect_links:
        links_by_pm.setdefault(link.pm_id, []).append(link)

    for task in pm_tasks:
        executions = lifecycle_years / task.interval_jaar if task.interval_jaar > 0 else 0.0

        if task.task_group_id:
            group = task_groups.get(task.task_group_id)
            if group is None:
                continue  # taakgroep ontbreekt — validators zullen dit melden
            if task.task_group_id not in counted_group_ids:
                # Kosten en downtime van de taakgroep éénmalig tellen
                group_executions = lifecycle_years / group.interval_jaar if group.interval_jaar > 0 else 0.0
                total_cost += group.cost_eur * group_executions
                if group.causes_unavailability:
                    downtime_per_exec = group.duration.to_hours() * group.unavailability_fraction
                    total_downtime_hr += downtime_per_exec * group_executions
                counted_group_ids.add(task.task_group_id)
            # Individuele taakoverwegingen (effectiviteit etc.) wel per FM
        else:
            # Los PM-taak — kosten en downtime volledig toerekenen aan dit FM
            total_cost += task.cost_eur * executions
            if task.causes_unavailability:
                downtime_per_exec = task.duration.to_hours() * task.unavailability_fraction
                total_downtime_hr += downtime_per_exec * executions

        # Effectklasse-bijdragen per PM-taak (onafhankelijk van groeplogica)
        for link in links_by_pm.get(task.pm_id, []):
            bijdrage = task.duration.to_hours() * link.fractie * executions
            pm_effect_bijdragen[link.klasse_id] = (
                pm_effect_bijdragen.get(link.klasse_id, 0.0) + bijdrage
            )

    return total_cost, total_downtime_hr, pm_effect_bijdragen


def _effect_bijdragen_per_jaar(
    *,
    faalmomenten: list[float],
    fm_effect_links: list[FMEffectLink] | None,
    pm_tasks: list[PMTask],
    pm_effect_links: list[PMEffectLink] | None,
    lifecycle_years: float,
) -> tuple[
    dict[str, list[float]],
    dict[str, list[float]],
    dict[str, list[float]],
]:
    """Jaarlijkse effectbijdragen; som per klasse ≈ lifecycle-totaal op FMResult.

    Returns (fm_per_jaar, pm_per_jaar, mixed_per_jaar).
    """
    num = len(faalmomenten)
    if num <= 0:
        return {}, {}, {}

    fm_out: dict[str, list[float]] = {}
    pm_out: dict[str, list[float]] = {}

    def _add(target: dict[str, list[float]], klasse_id: str, h: int, delta: float) -> None:
        if klasse_id not in target:
            target[klasse_id] = [0.0] * num
        target[klasse_id][h] += delta

    for link in fm_effect_links or []:
        for h, moment in enumerate(faalmomenten):
            _add(fm_out, link.klasse_id, h, float(moment) * float(link.fractie))

    links_by_pm: dict[str, list[PMEffectLink]] = {}
    for link in pm_effect_links or []:
        links_by_pm.setdefault(link.pm_id, []).append(link)

    for task in pm_tasks:
        for link in links_by_pm.get(task.pm_id, []):
            executions = (
                lifecycle_years / task.interval_jaar if task.interval_jaar > 0 else 0.0
            )
            lifecycle_bijdrage = task.duration.to_hours() * link.fractie * executions
            per_bucket = lifecycle_bijdrage / num if num > 0 else 0.0
            for h in range(num):
                _add(pm_out, link.klasse_id, h, per_bucket)

    mixed: dict[str, list[float]] = {}
    for klasse_id in set(fm_out) | set(pm_out):
        fm_series = fm_out.get(klasse_id, [0.0] * num)
        pm_series = pm_out.get(klasse_id, [0.0] * num)
        mixed[klasse_id] = [fm_series[h] + pm_series[h] for h in range(num)]

    return fm_out, pm_out, mixed


# ---------------------------------------------------------------------------
# Berekening per faalwijze
# ---------------------------------------------------------------------------

def compute_fm_result(
    fm: Faalwijze,
    pbs: PBSItem,
    pm_tasks: list[PMTask],
    task_groups: dict[str, TaskGroup],
    config: RCMConfig,
    counted_group_ids: Optional[set[str]] = None,
    fm_effect_links: Optional[list[FMEffectLink]] = None,
    pm_effect_links: Optional[list[PMEffectLink]] = None,
    all_pbs: Optional[dict[str, PBSItem]] = None,
) -> FMResult:
    """Bereken verwachte falingen, downtime en kosten voor één faalwijze."""
    # Gebruik effective_bouwjaar en effective_multiplicity als all_pbs beschikbaar is
    if all_pbs is not None:
        eff_bouwjaar = pbs.effective_bouwjaar(all_pbs)
        current_age = float(config.modeljaar - eff_bouwjaar) if eff_bouwjaar > 0 else 0.0
        eff_multiplicity = pbs.effective_multiplicity(all_pbs)
    else:
        current_age = pbs.current_age(config.modeljaar)
        eff_multiplicity = pbs.multiplicity

    lifecycle = effective_lifecycle_end_age(
        float(config.lifecycle_years),
        current_age,
        aw_mc_horizon=config.aw_mc_lifecycle_horizon,
    )

    # Verwacht aantal falingen
    rev_schedule = (
        build_rev_schedule(pm_tasks)
        if fm.failure_type.value == "aging"
        else ()
    )
    expected_failures = expected_failures_lifecycle(
        current_age=current_age,
        lifecycle_years=lifecycle,
        failure_type=fm.failure_type.value,
        mttf=fm.mttf_jaar,
        sigma=fm.effective_sigma(config.default_sigma_fraction),
        aging_distribution=fm.aging_distribution.value,
        beta_jaar=fm.beta_jaar,
        repair_quality=fm.repair_quality,
        rev_schedule=rev_schedule,
    )
    expected_failures *= eff_multiplicity  # vermenigvuldig met (effectieve) multipliciteit

    # P(minstens één faling) voor informatieve doeleinden
    p_fail = p_failure_by_age(
        t=lifecycle - current_age,
        failure_type=fm.failure_type.value,
        mttf=fm.mttf_jaar,
        sigma=fm.effective_sigma(config.default_sigma_fraction),
        aging_distribution=fm.aging_distribution.value,
        beta_jaar=fm.beta_jaar,
    )

    # Downtime door correctief onderhoud
    raw_downtime_hr = fm.downtime_per_failure.to_hours() * expected_failures

    # Detectievertraging (alleen bij niet-merkbaar falen)
    detection_delay_hr_per_failure = compute_detection_delay_hr(fm, pm_tasks)
    if detection_delay_hr_per_failure == float("inf"):
        # Geen inspectie aanwezig — gebruik 0 maar dit is een modelleerprobleem
        detection_delay_hr_per_failure = 0.0
    expected_detection_delay_hr = detection_delay_hr_per_failure * expected_failures

    total_downtime_hr = raw_downtime_hr + expected_detection_delay_hr

    # CM-kosten
    expected_cm_cost = fm.cost_cm_eur * expected_failures

    # PM-kosten, PM-downtime en PM-effectbijdragen
    pm_cost, pm_downtime_hr, pm_effect_bijdragen = compute_pm_totals(
        pm_tasks, task_groups, lifecycle, counted_group_ids,
        pm_effect_links=pm_effect_links,
    )

    # Risicobijdrage (bestaand veld, behouden voor backwards-compatibiliteit)
    risk_contribution = expected_failures * fm.p_ongewenste_gebeurtenis

    # FM-effectklasse-bijdragen: expected_failures × fractie per koppeling
    fm_effect_bijdragen: dict[str, float] = {}
    for link in (fm_effect_links or []):
        fm_effect_bijdragen[link.klasse_id] = expected_failures * link.fractie

    # Combineer FM- en PM-effectbijdragen
    combined_effect_bijdragen = dict(fm_effect_bijdragen)
    for klasse_id, uren in pm_effect_bijdragen.items():
        combined_effect_bijdragen[klasse_id] = (
            combined_effect_bijdragen.get(klasse_id, 0.0) + uren
        )

    faalmomenten = compute_fm_faalmomenten_per_bucket(
        config=config,
        fm=fm,
        pbs=pbs,
        pm_tasks=pm_tasks,
        all_pbs=all_pbs,
    )
    fm_effect_per_jaar, pm_effect_per_jaar, effect_per_jaar = _effect_bijdragen_per_jaar(
        faalmomenten=faalmomenten,
        fm_effect_links=fm_effect_links,
        pm_tasks=pm_tasks,
        pm_effect_links=pm_effect_links,
        lifecycle_years=lifecycle,
    )

    horizon_profile = build_fm_horizon_profile(
        config=config,
        fm=fm,
        pbs=pbs,
        pm_tasks=pm_tasks,
        all_pbs=all_pbs,
        hidden_nb_per_failure_hr=detection_delay_hr_per_failure,
    )

    return FMResult(
        fm_id=fm.fm_id,
        pbs_id=fm.pbs_id,
        p_failure_lifecycle=p_fail,
        expected_failures=expected_failures,
        expected_raw_downtime_hr=raw_downtime_hr,
        expected_detection_delay_hr=expected_detection_delay_hr,
        expected_total_downtime_hr=total_downtime_hr,
        expected_pm_downtime_hr=pm_downtime_hr,
        expected_cm_cost_eur=expected_cm_cost,
        pm_cost_eur=pm_cost,
        total_cost_eur=expected_cm_cost + pm_cost,
        risk_contribution=risk_contribution,
        effect_bijdragen=combined_effect_bijdragen,
        fm_effect_bijdragen=fm_effect_bijdragen,
        pm_effect_bijdragen=pm_effect_bijdragen,
        effect_bijdragen_per_jaar=effect_per_jaar,
        fm_effect_bijdragen_per_jaar=fm_effect_per_jaar,
        pm_effect_bijdragen_per_jaar=pm_effect_per_jaar,
        horizon_profile=horizon_profile,
    )


# ---------------------------------------------------------------------------
# Aggregatie per PBS-item
# ---------------------------------------------------------------------------

def compute_pbs_result(
    pbs: PBSItem,
    fm_results: list[FMResult],
    config: RCMConfig,
) -> PBSResult:
    """Aggregeer FM-resultaten naar een PBSResult."""
    lifecycle_hr = config.lifecycle_years * HOURS_PER_YEAR

    total_failures = sum(r.expected_failures for r in fm_results)
    total_downtime = sum(r.expected_total_downtime_hr + r.expected_pm_downtime_hr for r in fm_results)
    total_cm_cost = sum(r.expected_cm_cost_eur for r in fm_results)
    total_pm_cost = sum(r.pm_cost_eur for r in fm_results)
    total_cost = total_cm_cost + total_pm_cost
    total_risk = sum(r.risk_contribution for r in fm_results)

    unavailability_pct = (total_downtime / lifecycle_hr * 100.0) if lifecycle_hr > 0 else 0.0

    # Aggregeer effectklasse-bijdragen over alle FM-resultaten
    effect_bijdragen: dict[str, float] = {}
    for r in fm_results:
        for klasse_id, waarde in r.effect_bijdragen.items():
            effect_bijdragen[klasse_id] = effect_bijdragen.get(klasse_id, 0.0) + waarde

    return PBSResult(
        pbs_id=pbs.pbs_id,
        bouwdeel_naam=pbs.bouwdeel_naam,
        total_expected_failures=total_failures,
        total_downtime_hr=total_downtime,
        total_cm_cost_eur=total_cm_cost,
        total_pm_cost_eur=total_pm_cost,
        total_cost_eur=total_cost,
        unavailability_pct=unavailability_pct,
        total_risk_contribution=total_risk,
        fm_results=fm_results,
        effect_bijdragen=effect_bijdragen,
    )


def rank_pbs_results(pbs_results: dict[str, PBSResult]) -> list[PBSResult]:
    """Sorteer PBSResults aflopend op totaalkosten."""
    return sorted(pbs_results.values(), key=lambda r: r.total_cost_eur, reverse=True)


# ---------------------------------------------------------------------------
# Volledige projectberekening
# ---------------------------------------------------------------------------

def _compute_fm_result_worker(args: tuple) -> FMResult:
    """Worker-functie voor parallelle uitvoering via ProcessPoolExecutor."""
    fm_dict, pbs_dict, pm_dicts, tg_dicts, config_dict, fm_link_dicts, pm_link_dicts, all_pbs_dicts = args
    # Importeer lokaal om pickleability te garanderen
    from rcm_core.models import Faalwijze, FMEffectLink, PBSItem, PMEffectLink, PMTask, TaskGroup
    from rcm_core.config import RCMConfig
    fm = Faalwijze.from_dict(fm_dict)
    pbs = PBSItem.from_dict(pbs_dict)
    pm_tasks = [PMTask.from_dict(d) for d in pm_dicts]
    task_groups = {k: TaskGroup.from_dict(v) for k, v in tg_dicts.items()}
    config = RCMConfig.from_dict(config_dict)
    fm_effect_links = [FMEffectLink.from_dict(d) for d in fm_link_dicts]
    pm_effect_links = [PMEffectLink.from_dict(d) for d in pm_link_dicts]
    all_pbs = {k: PBSItem.from_dict(v) for k, v in all_pbs_dicts.items()}
    return compute_fm_result(
        fm, pbs, pm_tasks, task_groups, config,
        fm_effect_links=fm_effect_links,
        pm_effect_links=pm_effect_links,
        all_pbs=all_pbs,
    )


def deduplicate_parallel_fm_pm_costs(
    project: RCMProject,
    fm_results: dict[str, FMResult],
    *,
    fm_ids: Optional[list[str]] = None,
) -> dict[str, FMResult]:
    """Herbereken PM-velden met project-brede taakgroepdeduplicatie.

    Gebruik na parallelle worker-pool: zelfde FM-volgorde en ``compute_pm_totals``
    als het sequentiële pad. CM, faalmomenten en horizon_profile blijven uit workers.
    """
    target_ids = fm_ids if fm_ids is not None else list(project.faalwijzes.keys())
    order = [fid for fid in target_ids if fid in fm_results]
    counted_groups: set[str] = set()
    lifecycle = project.config.lifecycle_years
    updated = dict(fm_results)

    for fm_id in order:
        fm = project.faalwijzes.get(fm_id)
        if fm is None:
            continue
        prev = updated[fm_id]
        pm_tasks = project.get_pm_tasks_for_fm(fm_id)
        pm_effect_links = [
            link
            for pm in pm_tasks
            for link in project.get_pm_effect_links_for_pm(pm.pm_id)
        ]
        pm_cost, pm_downtime_hr, pm_effect_bijdragen = compute_pm_totals(
            pm_tasks,
            project.task_groups,
            lifecycle,
            counted_groups,
            pm_effect_links=pm_effect_links,
        )
        fm_effect_bijdragen: dict[str, float] = {}
        for link in project.get_fm_effect_links_for_fm(fm_id):
            fm_effect_bijdragen[link.klasse_id] = (
                prev.expected_failures * link.fractie
            )
        combined_effect_bijdragen = dict(fm_effect_bijdragen)
        for klasse_id, uren in pm_effect_bijdragen.items():
            combined_effect_bijdragen[klasse_id] = (
                combined_effect_bijdragen.get(klasse_id, 0.0) + uren
            )
        updated[fm_id] = replace(
            prev,
            pm_cost_eur=pm_cost,
            expected_pm_downtime_hr=pm_downtime_hr,
            total_cost_eur=prev.expected_cm_cost_eur + pm_cost,
            effect_bijdragen=combined_effect_bijdragen,
            fm_effect_bijdragen=fm_effect_bijdragen,
            pm_effect_bijdragen=pm_effect_bijdragen,
        )
    return updated


def compute_all_fm_results(
    project: RCMProject,
    fm_ids: Optional[list[str]] = None,
    parallel: bool = True,
) -> dict[str, FMResult]:
    """Bereken FMResult voor alle (of geselecteerde) faalwijzen.

    fm_ids=None → bereken alle faalwijzen.
    parallel=True → gebruik ProcessPoolExecutor voor snelheid (≥8 FM's).

    Taakgroep-PM wordt in sequentiële modus per FM gededupliceerd via een gedeelde
    ``counted_group_ids``. Bij parallelle pool volgt een post-pass
    (``deduplicate_parallel_fm_pm_costs``) met dezelfde volgorde en semantiek.
    """
    target_ids = fm_ids if fm_ids is not None else list(project.faalwijzes.keys())
    fms_to_calc = [project.faalwijzes[fid] for fid in target_ids if fid in project.faalwijzes]

    if not parallel or len(fms_to_calc) < 8:
        # Sequentieel — correct voor taakgroepdeduplicatie
        counted_groups: set[str] = set()
        results = {}
        for fm in fms_to_calc:
            pbs = project.pbs_items.get(fm.pbs_id)
            if pbs is None:
                continue
            pm_tasks = project.get_pm_tasks_for_fm(fm.fm_id)
            fm_effect_links = project.get_fm_effect_links_for_fm(fm.fm_id)
            pm_effect_links = [
                link for pm in pm_tasks
                for link in project.get_pm_effect_links_for_pm(pm.pm_id)
            ]
            results[fm.fm_id] = compute_fm_result(
                fm, pbs, pm_tasks, project.task_groups, project.config, counted_groups,
                fm_effect_links=fm_effect_links,
                pm_effect_links=pm_effect_links,
                all_pbs=project.pbs_items,
            )
        return results

    # Parallel — workers zonder gedeelde groep-set; post-pass dedupliceert PM
    all_pbs_dicts = {k: v.to_dict() for k, v in project.pbs_items.items()}
    work_items = []
    for fm in fms_to_calc:
        pbs = project.pbs_items.get(fm.pbs_id)
        if pbs is None:
            continue
        pm_tasks = project.get_pm_tasks_for_fm(fm.fm_id)
        fm_effect_links = project.get_fm_effect_links_for_fm(fm.fm_id)
        pm_effect_links = [
            link for pm in pm_tasks
            for link in project.get_pm_effect_links_for_pm(pm.pm_id)
        ]
        work_items.append((
            fm.to_dict(),
            pbs.to_dict(),
            [t.to_dict() for t in pm_tasks],
            {k: v.to_dict() for k, v in project.task_groups.items()},
            project.config.to_dict(),
            [l.to_dict() for l in fm_effect_links],
            [l.to_dict() for l in pm_effect_links],
            all_pbs_dicts,
        ))

    results = {}
    with ProcessPoolExecutor() as executor:
        future_to_fm = {
            executor.submit(_compute_fm_result_worker, item): item[0]["fm_id"]
            for item in work_items
        }
        for future in as_completed(future_to_fm):
            fm_id = future_to_fm[future]
            results[fm_id] = future.result()
    return deduplicate_parallel_fm_pm_costs(
        project, results, fm_ids=target_ids
    )


def compute_pbs_results(
    project: RCMProject,
    fm_results: dict[str, FMResult],
) -> dict[str, PBSResult]:
    """Aggregeer FM-resultaten per PBS-item."""
    pbs_results: dict[str, PBSResult] = {}
    for pbs_id, pbs in project.pbs_items.items():
        fm_list = [
            fm_results[fm.fm_id]
            for fm in project.get_faalwijzes_for_pbs(pbs_id)
            if fm.fm_id in fm_results
        ]
        if not fm_list:
            continue
        pbs_results[pbs_id] = compute_pbs_result(pbs, fm_list, project.config)
    return pbs_results


def run_analytical(
    project: RCMProject,
    fm_ids: Optional[list[str]] = None,
    parallel: bool = True,
) -> tuple[dict[str, FMResult], dict[str, PBSResult]]:
    """Volledige analytische berekening voor een project.

    Retourneert (fm_results, pbs_results). Geen classificatie meer (dropouts: zie
    `RCM2_REFERENTIE.md`); rangschikking is een UI-/presentatiebeslissing.
    """
    fm_results = compute_all_fm_results(project, fm_ids=fm_ids, parallel=parallel)
    pbs_results = compute_pbs_results(project, fm_results)
    return fm_results, pbs_results
