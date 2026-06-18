"""Invoer- en resultaatdiffs voor compare (slice 95 issues 05-06)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rcm_core.models import FMResult, RCMProject

_COMPARE_FIELDS = ("mttf_jaar", "failure_type", "faalwijze_omschrijving", "pbs_id")


@dataclass(frozen=True)
class FieldDiff:
    field: str
    value_a: Any
    value_b: Any
    difference_class: str


@dataclass(frozen=True)
class ResultDiff:
    metric: str
    value_a: float | None
    value_b: float | None


def _row_for_fm(project: RCMProject, fm_id: str) -> dict[str, Any] | None:
    fm = project.faalwijzes.get(fm_id)
    if fm is None:
        return None
    return {
        "mttf_jaar": fm.mttf_jaar,
        "failure_type": fm.failure_type,
        "faalwijze_omschrijving": fm.faalwijze_omschrijving,
        "pbs_id": fm.pbs_id,
    }


def _classify_field_diff(field: str, value_a: Any, value_b: Any) -> str:
    if field == "faalwijze_omschrijving" and value_a != value_b:
        return "terminologie"
    if field in ("mttf_jaar", "failure_type"):
        return "parameterisatie"
    if value_a != value_b:
        return "inhoud"
    return "inhoud"


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
    for field in _COMPARE_FIELDS:
        value = row.get(field)
        if side == "a":
            diffs.append(
                FieldDiff(
                    field=field,
                    value_a=value,
                    value_b=None,
                    difference_class="structuur",
                )
            )
        else:
            diffs.append(
                FieldDiff(
                    field=field,
                    value_a=None,
                    value_b=value,
                    difference_class="structuur",
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
    """All result metrics for a single-sided FM (detail panel for alleen A/B)."""
    fmr = _fm_result(project, fm_id, results)
    metrics = (
        ("total_cost_eur", fmr.total_cost_eur if fmr else None),
        ("expected_failures", fmr.expected_failures if fmr else None),
        ("expected_total_downtime_hr", fmr.expected_total_downtime_hr if fmr else None),
    )
    diffs: list[ResultDiff] = []
    for name, value in metrics:
        if side == "a":
            diffs.append(ResultDiff(metric=name, value_a=value, value_b=None))
        else:
            diffs.append(ResultDiff(metric=name, value_a=None, value_b=value))
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
    for field in _COMPARE_FIELDS:
        value_a = row_a.get(field)
        value_b = row_b.get(field)
        if value_a != value_b:
            diffs.append(
                FieldDiff(
                    field=field,
                    value_a=value_a,
                    value_b=value_b,
                    difference_class=_classify_field_diff(field, value_a, value_b),
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
    metrics = (
        ("total_cost_eur", fmr_a.total_cost_eur if fmr_a else None, fmr_b.total_cost_eur if fmr_b else None),
        (
            "expected_failures",
            fmr_a.expected_failures if fmr_a else None,
            fmr_b.expected_failures if fmr_b else None,
        ),
        (
            "expected_total_downtime_hr",
            fmr_a.expected_total_downtime_hr if fmr_a else None,
            fmr_b.expected_total_downtime_hr if fmr_b else None,
        ),
    )
    for name, val_a, val_b in metrics:
        if val_a != val_b:
            diffs.append(ResultDiff(metric=name, value_a=val_a, value_b=val_b))
    return tuple(diffs)
