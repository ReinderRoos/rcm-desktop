"""Declaratieve mapping van invoerbevindingen naar grid-kolommen (slice 88, Qt-vrij)."""

from __future__ import annotations

from typing import Any

from rcm_core.editing.persistence import build_project_from_state
from rcm_core.editing.schemas import ENTITY_SCHEMAS
from rcm_core.editing.validation import error_obj, normalize_key, set_row_error
from rcm_core.models import RCMProject
from rcm_core.validators import ValidationError, validate_aannamen, validate_project

from rcm_desktop.adapter.fm_edit_consistency import findings_for_edit_rows

INPUT_GRID_ENTITIES = frozenset({"faalwijzes", "pm_tasks", "effect_klassen", "task_groups"})

CROSS_ENTITY_PROJECT_RULES = frozenset(
    {
        "FM_NMF_REQUIRES_TEST",
        "PBS_EFFECTIVE_BOUWJAAR_ZERO",
        "PBS_BOUWJAAR_CHRONOLOGIE",
        "PBS_PARENT_CYCLE",
        "PBS_PARENT_FK",
        "FM_FUNC_FK",
        "PM_FM_FK",
        "PM_TG_FK",
        "EK_FUNC_FK",
        "FMEL_FM_FK",
        "FMEL_EK_FK",
        "PMEL_PM_FK",
        "PMEL_EK_FK",
        "FUNC_PBS_FK",
        "FM_PBS_FK",
    }
)

INJECTED_FINDING_CODES = frozenset(
    {
        "AGING_WITHOUT_REV",
        "REV_WITHOUT_AGING",
        "PM_BUNDLE_SUGGEST",
        *CROSS_ENTITY_PROJECT_RULES,
        "FM_RANDOM_SIGMA_NONZERO",
        "FM_SIGMA_NEGATIVE",
        "FM_COST_NEGATIVE",
        "FM_DOWNTIME_NEGATIVE",
        "FM_AGING_DISTRIBUTION_INVALID",
        "FM_WEIBULL_BETA_MISSING",
        "FM_REPAIR_QUALITY",
        "FM_P_OG",
        "PM_COST_NEGATIVE",
        "PM_INTERVAL_NONPOSITIVE",
        "PM_UNAVAIL_FRACTION",
        "TG_INTERVAL_NONPOSITIVE",
        "TG_COST_NEGATIVE",
        "FMEL_FRACTIE",
        "PMEL_FRACTIE",
        "AANNAME_LEEFTIJD_ONTBREEKT",
        "AANNAME_LEEFTIJD_GEERFDE",
        "AANNAME_FAALMODEL_ONTBREEKT",
        "AANNAME_CM_KOSTEN_ONTBREEKT",
        "AANNAME_PM_KOSTEN_ONTBREEKT",
        "PM_KOSTEN_HOGER_DAN_CM",
        "FRACTIE_ZONDER_MOTIVATIE",
        "BIBLIOTHEEK_REF_ONBEKEND",
    }
)

PROJECT_RULE_COLUMN: dict[str, tuple[str, str]] = {
    "FM_RANDOM_SIGMA_NONZERO": ("faalwijzes", "sigma_jaar"),
    "FM_SIGMA_NEGATIVE": ("faalwijzes", "sigma_jaar"),
    "FM_MTTF_NONPOSITIVE": ("faalwijzes", "mttf_jaar"),
    "FM_COST_NEGATIVE": ("faalwijzes", "cost_cm_eur"),
    "FM_DOWNTIME_NEGATIVE": ("faalwijzes", "downtime_per_failure"),
    "FM_REPAIR_QUALITY": ("faalwijzes", "repair_quality"),
    "FM_P_OG": ("faalwijzes", "p_ongewenste_gebeurtenis"),
    "FM_AGING_DISTRIBUTION_INVALID": ("faalwijzes", "aging_distribution"),
    "FM_WEIBULL_BETA_MISSING": ("faalwijzes", "beta_jaar"),
    "FM_NMF_REQUIRES_TEST": ("faalwijzes", "is_evident"),
    "FM_PBS_FK": ("faalwijzes", "pbs_id"),
    "FM_FUNC_FK": ("faalwijzes", "functie_id"),
    "PM_FM_FK": ("pm_tasks", "fm_id"),
    "PM_TG_FK": ("pm_tasks", "task_group_id"),
    "PM_INTERVAL_NONPOSITIVE": ("pm_tasks", "interval_jaar"),
    "PM_COST_NEGATIVE": ("pm_tasks", "cost_eur"),
    "PM_UNAVAIL_FRACTION": ("pm_tasks", "unavailability_fraction"),
    "TG_INTERVAL_NONPOSITIVE": ("task_groups", "interval_jaar"),
    "TG_COST_NEGATIVE": ("task_groups", "cost_eur"),
    "EK_FUNC_FK": ("effect_klassen", "functie_id"),
    "FMEL_FM_FK": ("fm_effect_links", "fm_id"),
    "FMEL_EK_FK": ("fm_effect_links", "klasse_id"),
    "FMEL_FRACTIE": ("fm_effect_links", "fractie"),
    "PMEL_PM_FK": ("pm_effect_links", "pm_id"),
    "PMEL_EK_FK": ("pm_effect_links", "klasse_id"),
    "PMEL_FRACTIE": ("pm_effect_links", "fractie"),
}

AANNAMEN_RULE_COLUMN: dict[str, tuple[str, str]] = {
    "AANNAME_LEEFTIJD_ONTBREEKT": ("pbs", "aanname_leeftijd"),
    "AANNAME_LEEFTIJD_GEERFDE": ("pbs", "aanname_leeftijd"),
    "AANNAME_FAALMODEL_ONTBREEKT": ("faalwijzes", "aanname_faalmodel"),
    "AANNAME_CM_KOSTEN_ONTBREEKT": ("faalwijzes", "aanname_cm_kosten"),
    "AANNAME_PM_KOSTEN_ONTBREEKT": ("pm_tasks", "aanname_kosten"),
    "PM_KOSTEN_HOGER_DAN_CM": ("pm_tasks", "aanname_kosten"),
    "FRACTIE_ZONDER_MOTIVATIE": ("fm_effect_links", "aanname_fractie"),
    "BIBLIOTHEEK_REF_ONBEKEND": ("faalwijzes", "library_ref"),
}

CONSISTENCY_RULE_COLUMN: dict[str, tuple[str, str]] = {
    "AGING_WITHOUT_REV": ("faalwijzes", "failure_type"),
    "REV_WITHOUT_AGING": ("faalwijzes", "failure_type"),
    "PM_BUNDLE_SUGGEST": ("pm_tasks", "task_group_id"),
}


def grid_severity_for_project_rule(code: str) -> str:
    if code in CROSS_ENTITY_PROJECT_RULES:
        return "warning"
    return "error"


def _strip_injected_findings(session: dict[str, Any]) -> None:
    edit_errors = session.get("edit_errors", {})
    for entity, rows in list(edit_errors.items()):
        for row_key, fields in list(rows.items()):
            for field, arr in list(fields.items()):
                kept = [e for e in arr if e.get("code") not in INJECTED_FINDING_CODES]
                if kept:
                    fields[field] = kept
                else:
                    del fields[field]
            if not fields:
                del rows[row_key]
        if not rows:
            edit_errors[entity] = {}


def _append_finding(
    session: dict[str, Any],
    entity: str,
    row_key: str,
    field: str,
    *,
    code: str,
    message: str,
    severity: str,
) -> None:
    row_key = normalize_key(row_key) or row_key
    bag = session.setdefault("edit_errors", {}).setdefault(entity, {})
    existing = bag.setdefault(row_key, {}).setdefault(field, [])
    if any(e.get("code") == code for e in existing):
        return
    set_row_error(
        bag,
        row_key,
        field,
        error_obj(code, message, field, row_key, entity, severity=severity),
    )


def _inject_validation_errors(
    session: dict[str, Any],
    items: list[ValidationError],
    column_map: dict[str, tuple[str, str]],
    *,
    default_severity: str | None = None,
) -> None:
    for item in items:
        mapping = column_map.get(item.code)
        if mapping is None:
            continue
        entity, field = mapping
        if entity not in INPUT_GRID_ENTITIES and entity not in ENTITY_SCHEMAS:
            continue
        if entity not in INPUT_GRID_ENTITIES:
            continue
        severity = default_severity or grid_severity_for_project_rule(item.code)
        _append_finding(
            session,
            entity,
            item.context,
            field,
            code=item.code,
            message=item.message,
            severity=severity,
        )


def _inject_consistency_findings(session: dict[str, Any]) -> None:
    current = session.get("edit_current", {})
    faalwijzen = list(current.get("faalwijzes", []))
    pm_tasks = list(current.get("pm_tasks", []))
    for row in faalwijzen:
        fm_id = normalize_key(row.get("fm_id"))
        if not fm_id:
            continue
        for finding in findings_for_edit_rows(fm_id, faalwijzen, pm_tasks):
            entity, field = CONSISTENCY_RULE_COLUMN[finding.code]
            row_key = fm_id
            if finding.code == "PM_BUNDLE_SUGGEST" and finding.related_pm_id:
                entity = "pm_tasks"
                row_key = finding.related_pm_id
            _append_finding(
                session,
                entity,
                row_key,
                field,
                code=finding.code,
                message=finding.message_nl,
                severity="warning",
            )


def inject_input_grid_findings(
    session: dict[str, Any],
    *,
    base_project: RCMProject,
) -> None:
    """Voeg buffer-brede bevindingen toe aan ``edit_errors`` (na pipeline-validatie)."""
    _strip_injected_findings(session)
    built = build_project_from_state(base_project, session=session)
    _inject_validation_errors(session, validate_project(built), PROJECT_RULE_COLUMN)
    _inject_validation_errors(
        session,
        validate_aannamen(built),
        AANNAMEN_RULE_COLUMN,
        default_severity="warning",
    )
    _inject_consistency_findings(session)
