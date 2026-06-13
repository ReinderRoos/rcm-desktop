"""View-state voor vergelijkingswerkruimte UI (slice 95 issue 07)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rcm_desktop.adapter.compare_balanced_presentation_service import (
    ComparePresentation,
    FailureModeDifference,
    build_compare_presentation,
)
from rcm_desktop.adapter.compare_diff_service import FieldDiff, ResultDiff
from rcm_desktop.adapter.compare_session_service import CompareSession


@dataclass(frozen=True)
class CompareWorkspaceRow:
    row_key: str
    match_kind: str
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
    if entry.pair.match_kind in ("unmatched_a", "unmatched_b"):
        return 0
    return len(entry.result_diffs)


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


def build_compare_workspace_view_state(session: CompareSession) -> CompareWorkspaceViewState:
    presentation = build_compare_presentation(session.project_a, session.project_b)
    return CompareWorkspaceViewState(
        path_a=session.path_a,
        path_b=session.path_b,
        label_a=session.path_a.name,
        label_b=session.path_b.name,
        rows=build_compare_workspace_rows(presentation),
    )
