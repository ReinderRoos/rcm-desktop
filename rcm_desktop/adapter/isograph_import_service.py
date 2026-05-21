"""Map Isograph RCM-Cost Excel export → RCMProject + import_settings (ADR-0004)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from rcm_core.import_settings_contract import normalize_import_settings
from rcm_core.isograph_pm_import_rules import (
    CauseEffectAssignmentRow,
    ScheduledTaskRow,
    fm_effect_fractie,
    pm_effect_fractie_default,
    pm_import_warning_unresolved,
    resolve_pm_task_id,
    should_create_fm_effect_link,
)
from rcm_core.models import (
    EffectKlasse,
    FailureType,
    FMEffectLink,
    Faalwijze,
    Functie,
    PBSItem,
    PMEffectLink,
    PMTask,
    RCMProject,
    TaskGroup,
    TaskType,
)
from rcm_core.config import RCMConfig
from rcm_core.units import TimeDuration, TimeUnit
from rcm_desktop.adapter.isograph_excel_reader import read_workbook_sheets

HOURS_PER_YEAR = 8760.0

_PROJECT_MC_PREFIXES = ("Avsim", "Npv", "Results")
_CAUSE_UNCERTAINTY_COLS = (
    "TotalCostErrPc",
    "TotalCostErrAbs",
    "EffectCostErrPc",
    "EffectCostErrAbs",
    "ITdtErrPc",
    "CTdtErrPc",
)


@dataclass(frozen=True)
class ImportConflict:
    pbs_id: str
    kind: str
    values: tuple[float, ...]


@dataclass
class ImportBuildResult:
    project: RCMProject
    import_settings: dict[str, Any]
    conflicts: list[ImportConflict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def build_from_workbook(path: Path, *, modeljaar: int) -> ImportBuildResult:
    sheets = read_workbook_sheets(path)
    return build_from_sheets(sheets, modeljaar=modeljaar)


def build_from_sheets(
    sheets: Mapping[str, list[dict[str, Any]]],
    *,
    modeljaar: int,
) -> ImportBuildResult:
    warnings: list[str] = []
    import_settings: dict[str, Any] = {"import_settings_schema_version": 1}
    ia_by_pbs: dict[str, set[float]] = {}

    config = _build_config(sheets.get("Project", []), modeljaar=modeljaar)
    import_settings["isograph_project"] = _extract_project_metadata(
        sheets.get("Project", [])
    )

    locations = {r["Id"]: r for r in sheets.get("RcmLocations", []) if r.get("Id")}
    cause_rows = [r for r in sheets.get("RcmCauses", []) if r.get("Id")]
    cause_location_ids = {
        str(r["LocationId"]).strip()
        for r in cause_rows
        if r.get("LocationId")
    }
    kept_location_ids = _prune_location_ids(locations, cause_location_ids)

    pbs_items = _build_pbs_items(locations, kept_location_ids)
    for row in cause_rows:
        loc = str(row.get("LocationId") or "").strip()
        if not loc:
            continue
        age_yr = _hours_to_years(row.get("InitialAge"))
        if age_yr is None:
            continue
        ia_by_pbs.setdefault(loc, set()).add(age_yr)

    conflicts = _initial_age_conflicts(ia_by_pbs)
    _apply_bouwjaar(pbs_items, ia_by_pbs, modeljaar, conflicts)

    ff_by_id = {r["Id"]: r for r in sheets.get("RcmFunctionalFailures", []) if r.get("Id")}
    functies = _build_functies(sheets.get("RcmFunctions", []), kept_location_ids)
    faalwijzes = _build_faalwijzes(
        cause_rows,
        ff_by_id,
        sheets.get("RcmCorrectiveTasks", []),
    )
    import_settings["isograph_causes"] = _extract_cause_metadata(cause_rows)

    effect_rows = sheets.get("RcmEffects", [])
    fm_by_id = {fm.fm_id: fm for fm in faalwijzes.values()}
    effect_klassen = _build_effect_klassen(effect_rows, fm_by_id)
    fm_effect_links, pm_effect_links, assignment_meta, assign_warnings = _build_effect_links(
        sheets.get("RcmCauseEffectAssignments", []),
        sheets.get("RcmScheduledTasks", []),
        fm_by_id,
    )
    warnings.extend(assign_warnings)
    if assignment_meta:
        import_settings["isograph_assignments"] = assignment_meta
    _align_effect_functies(effect_klassen, fm_effect_links, fm_by_id)

    scheduled_rows = sheets.get("RcmScheduledTasks", [])
    pm_tasks = _build_pm_tasks(scheduled_rows, faalwijzes)
    aw_disabled = _collect_aw_disabled_pm_ids(scheduled_rows, faalwijzes, pm_tasks)
    if aw_disabled:
        import_settings["aw_disabled_pm_ids"] = aw_disabled
    task_groups = _build_task_groups(sheets.get("TaskGroups", []))

    normalized_settings = normalize_import_settings(import_settings)
    project = RCMProject(
        config=config,
        pbs_items=pbs_items,
        functies=functies,
        faalwijzes=faalwijzes,
        pm_tasks=pm_tasks,
        task_groups=task_groups,
        effect_klassen=effect_klassen,
        fm_effect_links=fm_effect_links,
        pm_effect_links=pm_effect_links,
        import_settings=normalized_settings,
    )
    return ImportBuildResult(
        project=project,
        import_settings=normalized_settings,
        conflicts=conflicts,
        warnings=warnings,
    )


def _hours_to_years(raw: object) -> float | None:
    if raw is None or raw == "":
        return None
    return float(raw) / HOURS_PER_YEAR


def _build_config(project_rows: list[dict[str, Any]], *, modeljaar: int) -> RCMConfig:
    row = project_rows[0] if project_rows else {}
    lifetime = _hours_to_years(row.get("LifeTime")) or 80.0
    mc_n = int(row.get("RcmNoSimulations") or 10_000)
    seed_raw = row.get("RcmRandomNoSeed")
    seed = int(seed_raw) if seed_raw not in (None, "") else None
    return RCMConfig(
        lifecycle_years=lifetime,
        modeljaar=modeljaar,
        monte_carlo_n=mc_n,
        monte_carlo_seed=seed,
    )


def _extract_project_metadata(project_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not project_rows:
        return {}
    row = project_rows[0]
    out: dict[str, Any] = {}
    for key, value in row.items():
        if value is None:
            continue
        if key in ("LifeTime", "RcmNoSimulations", "RcmRandomNoSeed", "Id"):
            continue
        if key.startswith(_PROJECT_MC_PREFIXES) or key in ("Description", "FileName"):
            out[key] = value
    return out


def _extract_cause_metadata(cause_rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for row in cause_rows:
        fm_id = str(row.get("Id") or "").strip()
        if not fm_id:
            continue
        meta = {
            col: row[col]
            for col in _CAUSE_UNCERTAINTY_COLS
            if col in row and row[col] not in (None, "")
        }
        if meta:
            out[fm_id] = meta
    return out


def _prune_location_ids(
    locations: dict[str, dict[str, Any]],
    cause_location_ids: set[str],
) -> set[str]:
    kept: set[str] = set()
    for loc_id in cause_location_ids:
        current = loc_id
        while current:
            kept.add(current)
            parent_row = locations.get(current)
            if not parent_row:
                break
            parent = str(parent_row.get("Parent") or "").strip()
            current = parent if parent and parent != current else ""
    return kept


def _build_pbs_items(
    locations: dict[str, dict[str, Any]],
    kept_ids: set[str],
) -> dict[str, PBSItem]:
    items: dict[str, PBSItem] = {}
    for loc_id in sorted(kept_ids):
        row = locations.get(loc_id)
        if not row:
            continue
        parent = str(row.get("Parent") or "").strip() or None
        if parent and parent not in kept_ids:
            parent = None
        qty = row.get("Quantity")
        multiplicity = int(qty) if qty not in (None, "") else 1
        desc = str(row.get("Description") or loc_id)
        items[loc_id] = PBSItem(
            pbs_id=loc_id,
            object_naam=desc,
            element_naam=desc,
            bouwdeel_naam=desc,
            parent_pbs_id=parent,
            multiplicity=multiplicity,
        )
    return items


def _initial_age_conflicts(ia_by_pbs: dict[str, set[float]]) -> list[ImportConflict]:
    conflicts: list[ImportConflict] = []
    for pbs_id, ages in ia_by_pbs.items():
        if len(ages) > 1:
            conflicts.append(
                ImportConflict(
                    pbs_id=pbs_id,
                    kind="initial_age",
                    values=tuple(sorted(ages)),
                )
            )
    return conflicts


def _apply_bouwjaar(
    pbs_items: dict[str, PBSItem],
    ia_by_pbs: dict[str, set[float]],
    modeljaar: int,
    conflicts: list[ImportConflict],
) -> None:
    conflict_ids = {c.pbs_id for c in conflicts}
    for pbs_id, ages in ia_by_pbs.items():
        if pbs_id in conflict_ids or pbs_id not in pbs_items:
            continue
        age_yr = next(iter(ages))
        pbs_items[pbs_id].bouwjaar = int(modeljaar - age_yr)


def _build_functies(
    rows: list[dict[str, Any]],
    kept_pbs_ids: set[str],
) -> dict[str, Functie]:
    out: dict[str, Functie] = {}
    for row in rows:
        fid = str(row.get("Id") or "").strip()
        parent = str(row.get("Parent") or "").strip()
        if not fid or parent not in kept_pbs_ids:
            continue
        out[fid] = Functie(
            functie_id=fid,
            pbs_id=parent,
            functie_omschrijving=str(row.get("Description") or fid),
        )
    return out


def _build_faalwijzes(
    cause_rows: list[dict[str, Any]],
    ff_by_id: dict[str, dict[str, Any]],
    corrective_rows: list[dict[str, Any]],
) -> dict[str, Faalwijze]:
    cm_by_cause: dict[str, dict[str, Any]] = {}
    for row in corrective_rows:
        cid = str(row.get("Cause") or "").strip()
        if cid:
            cm_by_cause[cid] = row

    out: dict[str, Faalwijze] = {}
    for row in cause_rows:
        fm_id = str(row.get("Id") or "").strip()
        if not fm_id or row.get("FmMttf") in (None, ""):
            continue
        ff_id = str(row.get("Parent") or "").strip()
        ff = ff_by_id.get(ff_id, {})
        functie_id = str(ff.get("Parent") or "").strip()
        pbs_id = str(row.get("LocationId") or "").strip()
        mttf = _hours_to_years(row.get("FmMttf")) or 0.0
        sigma = _hours_to_years(row.get("FmStd")) or 0.0
        mttr_h = float(row.get("Mttr") or 0.0)
        cm = cm_by_cause.get(fm_id, {})
        cost_cm = float(cm.get("OperationalCost") or 0.0)
        out[fm_id] = Faalwijze(
            fm_id=fm_id,
            pbs_id=pbs_id,
            functie_id=functie_id,
            faalwijze_omschrijving=str(row.get("Description") or fm_id),
            eindgevolg=str(ff.get("Description") or ""),
            failure_type=_map_failure_type(row.get("FmDistribution")),
            mttf_jaar=mttf,
            sigma_jaar=sigma,
            downtime_per_failure=TimeDuration(mttr_h, TimeUnit.HOURS),
            cost_cm_eur=cost_cm,
        )
    return out


def _map_failure_type(raw: object) -> FailureType:
    dist = str(raw or "").strip().lower()
    if dist in {"normal", "weibull", "lognormal"}:
        return FailureType.AGING
    return FailureType.RANDOM


def _build_effect_klassen(
    effect_rows: list[dict[str, Any]],
    fm_by_id: dict[str, Faalwijze],
) -> dict[str, EffectKlasse]:
    default_functie = next(iter(fm_by_id.values())).functie_id if fm_by_id else ""
    out: dict[str, EffectKlasse] = {}
    for row in effect_rows:
        eid = str(row.get("Id") or "").strip()
        if not eid:
            continue
        out[eid] = EffectKlasse(
            klasse_id=eid,
            omschrijving=str(row.get("Description") or eid),
            functie_id=default_functie,
            categorie=str(row.get("Type") or ""),
            cost_gevolg_eur=0.0,
        )
    return out


def _build_effect_links(
    assignment_rows: list[dict[str, Any]],
    scheduled_rows: list[dict[str, Any]],
    fm_by_id: dict[str, Faalwijze],
) -> tuple[
    dict[str, FMEffectLink],
    dict[str, PMEffectLink],
    dict[str, Any],
    list[str],
]:
    tasks = [
        ScheduledTaskRow(
            cause_id=str(r.get("Cause") or ""),
            sub_index=r.get("SubIndex", 0),
            task_id=str(r.get("TaskId") or ""),
            task_type=str(r.get("Type") or ""),
            enabled=r.get("Enabled", True),
        )
        for r in scheduled_rows
        if r.get("Cause")
    ]
    fm_links: dict[str, FMEffectLink] = {}
    pm_links: dict[str, PMEffectLink] = {}
    assignment_meta: dict[str, Any] = {}
    warnings: list[str] = []

    for row in assignment_rows:
        cause = str(row.get("Cause") or "").strip()
        effect = str(row.get("Effect") or "").strip()
        if not cause or not effect or cause not in fm_by_id:
            continue
        aer = CauseEffectAssignmentRow(
            cause_id=cause,
            effect_id=effect,
            c_enable=row.get("CEnable"),
            p_enable=row.get("PEnable"),
            i_enable=row.get("IEnable"),
            redundancy_factor=row.get("RedundancyFactor"),
            sub_index=row.get("SubIndex", 0),
        )
        if should_create_fm_effect_link(aer):
            link_id = f"FMEL|{cause}|{effect}|{row.get('SubIndex', 0)}"
            fm_links[link_id] = FMEffectLink(
                link_id=link_id,
                fm_id=cause,
                klasse_id=effect,
                fractie=fm_effect_fractie(aer),
            )
        pm_task_key = resolve_pm_task_id(aer, tasks)
        if pm_task_key:
            pm_id = f"{cause}|{pm_task_key}|{aer.sub_index}"
            link_id = f"PMEL|{pm_id}|{effect}"
            pm_links[link_id] = PMEffectLink(
                link_id=link_id,
                pm_id=pm_id,
                klasse_id=effect,
                fractie=pm_effect_fractie_default(),
            )
        else:
            warn = pm_import_warning_unresolved(aer)
            if warn:
                warnings.append(warn)
            if _truthy(aer.p_enable) or _truthy(aer.i_enable):
                key = f"{cause}|{effect}|{row.get('SubIndex', 0)}"
                assignment_meta[key] = {
                    "PEnable": row.get("PEnable"),
                    "IEnable": row.get("IEnable"),
                    "CEnable": row.get("CEnable"),
                    "SubIndex": row.get("SubIndex"),
                }

    return fm_links, pm_links, assignment_meta, warnings


def _align_effect_functies(
    effect_klassen: dict[str, EffectKlasse],
    fm_links: dict[str, FMEffectLink],
    fm_by_id: dict[str, Faalwijze],
) -> None:
    for link in fm_links.values():
        fm = fm_by_id.get(link.fm_id)
        ek = effect_klassen.get(link.klasse_id)
        if fm and ek and not ek.functie_id:
            ek.functie_id = fm.functie_id
        elif fm and ek and ek.functie_id == "":
            ek.functie_id = fm.functie_id


def _scheduled_task_pm_id(row: dict[str, Any]) -> str | None:
    cause = str(row.get("Cause") or "").strip()
    if not cause:
        return None
    task_id = str(row.get("TaskId") or "PM")
    sub = str(row.get("SubIndex", 0)).strip()
    return f"{cause}|{task_id}|{sub}"


def _collect_aw_disabled_pm_ids(
    scheduled_rows: list[dict[str, Any]],
    faalwijzes: dict[str, Faalwijze],
    pm_tasks: dict[str, PMTask],
) -> list[str]:
    """AW Enabled=False → pm_ids for planning overlay (scenario, not structural link)."""
    disabled: list[str] = []
    for row in scheduled_rows:
        cause = str(row.get("Cause") or "").strip()
        if not cause or cause not in faalwijzes:
            continue
        if _truthy(row.get("Enabled", True)):
            continue
        pm_id = _scheduled_task_pm_id(row)
        if pm_id and pm_id in pm_tasks:
            disabled.append(pm_id)
    return sorted(set(disabled))


def _build_pm_tasks(
    scheduled_rows: list[dict[str, Any]],
    faalwijzes: dict[str, Faalwijze],
) -> dict[str, PMTask]:
    out: dict[str, PMTask] = {}
    for row in scheduled_rows:
        cause = str(row.get("Cause") or "").strip()
        if not cause or cause not in faalwijzes:
            continue
        pm_id = _scheduled_task_pm_id(row)
        if not pm_id:
            continue
        task_id = str(row.get("TaskId") or "PM")
        interval_h = float(row.get("TaskInterval") or row.get("OptimizationInitialInterval") or 0)
        interval_yr = interval_h / HOURS_PER_YEAR if interval_h else 1.0
        duration_h = float(row.get("TaskDuration") or 0.0)
        cost = float(row.get("OperationalCost") or 0.0)
        desc = str(row.get("Description") or "")
        aw_type = str(row.get("Type") or "")
        is_wet = (
            "WET" in aw_type.upper()
            or "WET" in task_id.upper()
            or "WET" in desc.upper()
        )
        out[pm_id] = PMTask(
            pm_id=pm_id,
            fm_id=cause,
            taak_type=_map_task_type(row.get("Type"), task_id),
            taak_omschrijving=desc,
            interval_jaar=interval_yr,
            duration=TimeDuration(duration_h, TimeUnit.HOURS),
            cost_eur=cost,
            causes_unavailability=_truthy(row.get("OutedDuringMaintenance")),
            is_wettelijk_verplicht=is_wet,
        )
    return out


def _map_task_type(aw_type: object, task_id: str) -> TaskType:
    t = str(aw_type or "").strip()
    tid = str(task_id or "").strip().upper()
    if tid == "REV" or "REV" in tid:
        return TaskType.REV
    if t in _IN_TASK_TYPES or tid in {"IN", "INSPECTION"}:
        return TaskType.IN
    if tid == "TST" or "TST" in tid:
        return TaskType.TST
    return TaskType.SVO


_IN_TASK_TYPES = frozenset({"Inspection", "IN", "Inspectie"})


def _build_task_groups(rows: list[dict[str, Any]]) -> dict[str, TaskGroup]:
    out: dict[str, TaskGroup] = {}
    for row in rows:
        gid = str(row.get("Id") or "").strip()
        if not gid:
            continue
        interval_h = float(row.get("TaskInterval") or 0)
        out[gid] = TaskGroup(
            group_id=gid,
            omschrijving=str(row.get("Description") or gid),
            taak_type=_map_task_type(row.get("Type"), gid),
            interval_jaar=interval_h / HOURS_PER_YEAR if interval_h else 1.0,
        )
    return out


def _truthy(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
