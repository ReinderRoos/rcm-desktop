"""View-state voor vergelijkingswerkruimte UI (slice 95 issue 07, slice 96)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rcm_desktop.adapter.compare_balanced_presentation_service import (
    ComparePresentation,
    FailureModeDifference,
    build_compare_presentation,
)
from rcm_desktop.adapter.compare_diff_service import FieldDiff, ResultDiff
from rcm_desktop.adapter.compare_results_service import CompareResultsBundle
from rcm_desktop.adapter.compare_session_service import CompareSession

MATCH_KIND_BADGE_LABELS: dict[str, str] = {
    "id": "ID",
    "fingerprint": "FP",
    "unmatched_a": "A",
    "unmatched_b": "B",
}


def match_kind_badge(match_kind: str) -> str:
    return MATCH_KIND_BADGE_LABELS.get(match_kind, match_kind)


@dataclass(frozen=True)
class CompareWorkspaceRow:
    row_key: str
    match_kind: str
    match_badge: str
    fm_id_a: str | None
    fm_id_b: str | None
    status_label: str
    difference_class: str
    field_diff_count: int
    result_diff_count: int
    field_diffs: tuple[FieldDiff, ...]
    result_diffs: tuple[ResultDiff, ...]


@dataclass(frozen=True)
class CompareWorkspaceViewState:
    path_a: Path
    path_b: Path
    label_a: str
    label_b: str
    run_source_a: str
    run_source_b: str
    rows: tuple[CompareWorkspaceRow, ...]


def _status_label(match_kind: str) -> str:
    if match_kind == "unmatched_a":
        return "alleen A"
    if match_kind == "unmatched_b":
        return "alleen B"
    return "beide"


def _field_diff_count(entry: FailureModeDifference) -> int:
    if entry.pair.match_kind in ("unmatched_a", "unmatched_b"):
        return 0
    return len(entry.field_diffs)


def _result_diff_count(entry: FailureModeDifference) -> int:
    return sum(1 for diff in entry.result_diffs if diff.is_different)


def _row_key(entry: FailureModeDifference) -> str:
    pair = entry.pair
    if pair.fm_id_a and pair.fm_id_b:
        return f"{pair.fm_id_a}|{pair.fm_id_b}"
    if pair.fm_id_a:
        return f"a:{pair.fm_id_a}"
    if pair.fm_id_b:
        return f"b:{pair.fm_id_b}"
    return "unknown"


def build_compare_workspace_rows(
    presentation: ComparePresentation,
) -> tuple[CompareWorkspaceRow, ...]:
    rows: list[CompareWorkspaceRow] = []
    for entry in presentation.entries:
        rows.append(
            CompareWorkspaceRow(
                row_key=_row_key(entry),
                match_kind=entry.pair.match_kind,
                match_badge=match_kind_badge(entry.pair.match_kind),
                fm_id_a=entry.pair.fm_id_a,
                fm_id_b=entry.pair.fm_id_b,
                status_label=_status_label(entry.pair.match_kind),
                difference_class=entry.difference_class,
                field_diff_count=_field_diff_count(entry),
                result_diff_count=_result_diff_count(entry),
                field_diffs=entry.field_diffs,
                result_diffs=entry.result_diffs,
            )
        )
    return tuple(rows)


def build_compare_workspace_view_state(
    session: CompareSession,
    *,
    results_bundle: CompareResultsBundle | None = None,
) -> CompareWorkspaceViewState:
    bundle = results_bundle
    presentation = build_compare_presentation(
        session.project_a,
        session.project_b,
        results_a=None if bundle is None else bundle.results_a or None,
        results_b=None if bundle is None else bundle.results_b or None,
    )
    return CompareWorkspaceViewState(
        path_a=session.path_a,
        path_b=session.path_b,
        label_a=session.path_a.name,
        label_b=session.path_b.name,
        run_source_a=bundle.status_a.source if bundle else "none",
        run_source_b=bundle.status_b.source if bundle else "none",
        rows=build_compare_workspace_rows(presentation),
    )
