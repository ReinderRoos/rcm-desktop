from __future__ import annotations

from typing import Any, TypedDict

import pandas as pd

from rcm_core.editing.schemas import ENTITY_SCHEMAS
from rcm_core.models import RCMProject


class ErrorObj(TypedDict):
    code: str
    severity: str
    message: str
    field: str
    row_key: str
    entity: str


ErrorState = dict[str, dict[str, list[ErrorObj]]]


def normalize_key(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def coerce_value(value: Any, expected: str) -> tuple[Any, bool]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None, True
    if expected == "str":
        return str(value), True
    if expected == "int":
        try:
            if str(value).strip() == "":
                return None, True
            return int(float(value)), True
        except Exception:
            return value, False
    if expected == "float":
        try:
            if str(value).strip() == "":
                return None, True
            return float(value), True
        except Exception:
            return value, False
    if expected == "bool":
        if isinstance(value, bool):
            return value, True
        sval = str(value).strip().lower()
        if sval in ("1", "true", "ja", "yes"):
            return True, True
        if sval in ("0", "false", "nee", "no"):
            return False, True
        return value, False
    if expected == "dict":
        if isinstance(value, dict):
            return value, True
        return value, False
    return value, True


def error_obj(code: str, message: str, field: str, row_key: str, entity: str, severity: str = "error") -> ErrorObj:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "field": field,
        "row_key": row_key,
        "entity": entity,
    }


def set_row_error(error_bag: ErrorState, row_key: str, field: str, err: ErrorObj) -> None:
    error_bag.setdefault(row_key, {}).setdefault(field, []).append(err)


def resolve_fk_set(project: RCMProject, edit_current: dict[str, list[dict[str, Any]]], target: str) -> set[str]:
    if target in ENTITY_SCHEMAS:
        key_field = ENTITY_SCHEMAS[target]["key_field"]
        return {normalize_key(r.get(key_field)) for r in edit_current.get(target, []) if normalize_key(r.get(key_field))}
    if target == "functies":
        return set(project.functies.keys())
    if target == "task_groups":
        return set(project.task_groups.keys())
    return set()


def validate_entity_rows(
    entity: str,
    rows: list[dict[str, Any]],
    project: RCMProject,
    edit_current: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], ErrorState]:
    schema = ENTITY_SCHEMAS[entity]
    key_field: str = schema["key_field"]
    required_fields: list[str] = schema["required_fields"]
    field_types: dict[str, str] = schema["field_types"]
    fk_rules: dict[str, str] = schema["fk_rules"]
    error_bag: ErrorState = {}
    coerced_rows: list[dict[str, Any]] = []

    for idx, row in enumerate(rows):
        row2 = dict(row)
        row_key = normalize_key(row2.get(key_field)) or f"row-{idx+1}"

        for field in required_fields:
            if normalize_key(row2.get(field)) == "":
                set_row_error(
                    error_bag,
                    row_key,
                    field,
                    error_obj("REQUIRED_FIELD", f"Verplicht veld '{field}' ontbreekt", field, row_key, entity),
                )

        for field, type_name in field_types.items():
            if field in row2:
                coerced, ok = coerce_value(row2.get(field), type_name)
                row2[field] = coerced
                if not ok:
                    set_row_error(
                        error_bag,
                        row_key,
                        field,
                        error_obj("TYPE_CHECK", f"Typefout in veld '{field}' (verwacht {type_name})", field, row_key, entity),
                    )

        for field, target in fk_rules.items():
            fk_val = normalize_key(row2.get(field))
            if fk_val == "":
                continue
            fk_set = resolve_fk_set(project, edit_current, target)
            if fk_val not in fk_set:
                code = "FK_CHECK"
                if entity == "faalwijzes" and field == "pbs_id":
                    code = "FM_PBS_FK"
                elif entity == "pm_tasks" and field == "fm_id":
                    code = "PM_FM_FK"
                set_row_error(
                    error_bag,
                    row_key,
                    field,
                    error_obj(code, f"'{field}' verwijst naar onbekende waarde '{fk_val}'", field, row_key, entity),
                )

        if entity == "pbs":
            if row2.get("multiplicity") is not None and row2.get("multiplicity", 1) < 1:
                set_row_error(
                    error_bag,
                    row_key,
                    "multiplicity",
                    error_obj("PBS_MULTIPLICITY", "multiplicity moet >= 1 zijn", "multiplicity", row_key, entity),
                )
        if entity == "faalwijzes":
            mttf = row2.get("mttf_jaar")
            if isinstance(mttf, (int, float)) and mttf <= 0:
                set_row_error(
                    error_bag,
                    row_key,
                    "mttf_jaar",
                    error_obj("FM_MTTF_NONPOSITIVE", "mttf_jaar moet > 0 zijn", "mttf_jaar", row_key, entity),
                )
            if row2.get("repair_quality") is not None:
                rq = row2.get("repair_quality")
                if isinstance(rq, (int, float)) and not (0.0 <= rq <= 1.0):
                    set_row_error(
                        error_bag,
                        row_key,
                        "repair_quality",
                        error_obj("FM_REPAIR_QUALITY", "repair_quality moet tussen 0 en 1 liggen", "repair_quality", row_key, entity),
                    )
        if entity in ("fm_effect_links", "pm_effect_links"):
            fractie = row2.get("fractie")
            if isinstance(fractie, (int, float)) and not (0.0 <= fractie <= 1.0):
                set_row_error(
                    error_bag,
                    row_key,
                    "fractie",
                    error_obj(
                        "EFFECT_FRACTION",
                        "fractie moet tussen 0 en 1 liggen",
                        "fractie",
                        row_key,
                        entity,
                    ),
                )
        if entity == "pm_tasks":
            interval = row2.get("interval_jaar")
            if isinstance(interval, (int, float)) and interval <= 0:
                set_row_error(
                    error_bag,
                    row_key,
                    "interval_jaar",
                    error_obj("PM_INTERVAL_NONPOSITIVE", "interval_jaar moet > 0 zijn", "interval_jaar", row_key, entity),
                )
            uf = row2.get("unavailability_fraction")
            if isinstance(uf, (int, float)) and not (0.0 <= uf <= 1.0):
                set_row_error(
                    error_bag,
                    row_key,
                    "unavailability_fraction",
                    error_obj("PM_UNAVAIL_FRACTION", "unavailability_fraction moet tussen 0 en 1 liggen", "unavailability_fraction", row_key, entity),
                )

        coerced_rows.append(row2)
    return coerced_rows, error_bag

