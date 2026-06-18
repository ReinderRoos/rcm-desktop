"""Invoer- en resultaatdiffs voor compare (slice 95 issues 05-06, slice 96 issues 03-04)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rcm_core.editing.schemas import ENTITY_SCHEMAS
from rcm_core.models import FMResult, RCMProject

_COMPARE_EXCLUDED = frozenset({"fm_id", "library_ref", "notes", "downtime_per_failure"})
_US16_METRICS = ("total_cost_eur", "expected_total_downtime_hr", "risk_contribution")


def compare_field_names() -> tuple[str, ...]:
    """Schema-gedreven faalwijze-velden minus vaste exclusions (slice 96 issue 03)."""
    names: list[str] = []
    for field in ENTITY_SCHEMAS["faalwijzes"]["field_types"]:
        if field in _COMPARE_EXCLUDED or field.startswith("aanname_"):
            continue
        names.append(field)
    return tuple(names)


def _field_value(fm, field: str) -> Any:
    value = getattr(fm, field)
    if hasattr(value, "value"):
        return value.value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


def _row_for_fm(project: RCMProject, fm_id: str) -> dict[str, Any] | None:
    fm = project.faalwijzes.get(fm_id)
    if fm is None:
        return None
    return {field: _field_value(fm, field) for field in compare_field_names()}


def _classify_field_diff(field: str, value_a: Any, value_b: Any) -> str:
    if field == "faalwijze_omschrijving" and value_a != value_b:
        return "terminologie"
    if field in ("mttf_jaar", "failure_type", "sigma_jaar", "beta_jaar", "aging_distribution"):
        return "parameterisatie"
    if value_a != value_b:
        return "inhoud"
    return "inhoud"


@dataclass(frozen=True)
class FieldDiff:
    field: str
    value_a: Any
    value_b: Any
    difference_class: str
    is_different: bool = True


@dataclass(frozen=True)
class ResultDiff:
    metric: str
    value_a: float | None
    value_b: float | None
    is_different: bool = False


def build_unmatched_field_values(
    project: RCMProject,
    fm_id: str,
    *,
    side: str,
) -> tuple[FieldDiff, ...]:
    """All compare fields for a single-sided FM (detail panel for alleen A/B)."""
    row = _row_for_fm(project, fm_id)
    if row is None:
        return ()
    diffs: list[FieldDiff] = []
    for field in compare_field_names():
        value = row.get(field)
        if side == "a":
            diffs.append(
                FieldDiff(
                    field=field,
                    value_a=value,
                    value_b=None,
                    difference_class="structuur",
                    is_different=True,
                )
            )
        else:
            diffs.append(
                FieldDiff(
                    field=field,
                    value_a=None,
                    value_b=value,
                    difference_class="structuur",
                    is_different=True,
                )
            )
    return tuple(diffs)


def build_unmatched_result_values(
    project: RCMProject,
    fm_id: str,
    *,
    side: str,
    results: dict[str, FMResult] | None = None,
) -> tuple[ResultDiff, ...]:
    """All US16 result metrics for a single-sided FM."""
    fmr = _fm_result(project, fm_id, results)
    diffs: list[ResultDiff] = []
    for name in _US16_METRICS:
        value = getattr(fmr, name, None) if fmr else None
        if side == "a":
            diffs.append(ResultDiff(metric=name, value_a=value, value_b=None, is_different=value is not None))
        else:
            diffs.append(ResultDiff(metric=name, value_a=None, value_b=value, is_different=value is not None))
    return tuple(diffs)


def build_field_diffs(
    project_a: RCMProject,
    project_b: RCMProject,
    *,
    fm_id_a: str,
    fm_id_b: str,
) -> tuple[FieldDiff, ...]:
    row_a = _row_for_fm(project_a, fm_id_a)
    row_b = _row_for_fm(project_b, fm_id_b)
    if row_a is None or row_b is None:
        return ()
    diffs: list[FieldDiff] = []
    for field in compare_field_names():
        value_a = row_a.get(field)
        value_b = row_b.get(field)
        if value_a != value_b:
            diffs.append(
                FieldDiff(
                    field=field,
                    value_a=value_a,
                    value_b=value_b,
                    difference_class=_classify_field_diff(field, value_a, value_b),
                    is_different=True,
                )
            )
    return tuple(diffs)


def _fm_result(project: RCMProject, fm_id: str, results: dict[str, FMResult] | None) -> FMResult | None:
    if results is None:
        return None
    return results.get(fm_id)


def build_result_diffs(
    project_a: RCMProject,
    project_b: RCMProject,
    *,
    fm_id_a: str,
    fm_id_b: str,
    results_a: dict[str, FMResult] | None = None,
    results_b: dict[str, FMResult] | None = None,
) -> tuple[ResultDiff, ...]:
    fmr_a = _fm_result(project_a, fm_id_a, results_a)
    fmr_b = _fm_result(project_b, fm_id_b, results_b)
    diffs: list[ResultDiff] = []
    for name in _US16_METRICS:
        val_a = getattr(fmr_a, name, None) if fmr_a else None
        val_b = getattr(fmr_b, name, None) if fmr_b else None
        if val_a is not None or val_b is not None:
            diffs.append(
                ResultDiff(
                    metric=name,
                    value_a=val_a,
                    value_b=val_b,
                    is_different=val_a != val_b,
                )
            )
    return tuple(diffs)
