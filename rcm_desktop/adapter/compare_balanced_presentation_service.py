"""Balanced compare presentation DTO (slice 95 issue 06)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import FMResult, RCMProject

from rcm_desktop.adapter.compare_align_service import FailureModePair, align_failure_modes
from rcm_desktop.adapter.compare_diff_service import (
    FieldDiff,
    ResultDiff,
    build_field_diffs,
    build_result_diffs,
    build_unmatched_field_values,
    build_unmatched_result_values,
)


@dataclass(frozen=True)
class FailureModeDifference:
    pair: FailureModePair
    field_diffs: tuple[FieldDiff, ...]
    result_diffs: tuple[ResultDiff, ...]
    difference_class: str


@dataclass(frozen=True)
class ComparePresentation:
    entries: tuple[FailureModeDifference, ...]


def _overall_class(field_diffs: tuple[FieldDiff, ...], pair: FailureModePair) -> str:
    if pair.match_kind in ("unmatched_a", "unmatched_b"):
        return "structuur"
    if not field_diffs:
        return "inhoud"
    classes = {d.difference_class for d in field_diffs}
    if "parameterisatie" in classes:
        return "parameterisatie"
    if "terminologie" in classes:
        return "terminologie"
    return field_diffs[0].difference_class


def build_compare_presentation(
    project_a: RCMProject,
    project_b: RCMProject,
    *,
    results_a: dict[str, FMResult] | None = None,
    results_b: dict[str, FMResult] | None = None,
) -> ComparePresentation:
    pairs = align_failure_modes(project_a, project_b)
    entries: list[FailureModeDifference] = []
    for pair in pairs:
        field_diffs: tuple[FieldDiff, ...] = ()
        result_diffs: tuple[ResultDiff, ...] = ()
        if pair.fm_id_a and pair.fm_id_b:
            field_diffs = build_field_diffs(
                project_a, project_b, fm_id_a=pair.fm_id_a, fm_id_b=pair.fm_id_b
            )
            result_diffs = build_result_diffs(
                project_a,
                project_b,
                fm_id_a=pair.fm_id_a,
                fm_id_b=pair.fm_id_b,
                results_a=results_a,
                results_b=results_b,
            )
        elif pair.match_kind == "unmatched_a" and pair.fm_id_a:
            field_diffs = build_unmatched_field_values(project_a, pair.fm_id_a, side="a")
            result_diffs = build_unmatched_result_values(
                project_a,
                pair.fm_id_a,
                side="a",
                results=results_a,
            )
        elif pair.match_kind == "unmatched_b" and pair.fm_id_b:
            field_diffs = build_unmatched_field_values(project_b, pair.fm_id_b, side="b")
            result_diffs = build_unmatched_result_values(
                project_b,
                pair.fm_id_b,
                side="b",
                results=results_b,
            )
        entries.append(
            FailureModeDifference(
                pair=pair,
                field_diffs=field_diffs,
                result_diffs=result_diffs,
                difference_class=_overall_class(field_diffs, pair),
            )
        )
    return ComparePresentation(entries=tuple(entries))
