"""Preview selection session — filter, bulk, apply-eligible set (slice 54, Qt-vrij)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from rcm_desktop import messages
from rcm_desktop.adapter.meekoppel_apply_service import MeekoppelAnchor
from rcm_desktop.adapter.meekoppel_bundle_insight_service import (
    MeekoppelPreviewTaskRow,
    live_determined_by_line,
    live_target_year,
    recompute_task_rows_for_selection,
)

VisibilityFilter = Literal["all", "shifting_only"]


def is_shiftable(row: MeekoppelPreviewTaskRow) -> bool:
    return row.blocked_reason is None


def _is_visible(row: MeekoppelPreviewTaskRow, visibility_filter: VisibilityFilter) -> bool:
    if visibility_filter == "all":
        return True
    if row.blocked_reason is not None:
        return True
    return row.delta_years != 0


@dataclass(frozen=True)
class MeekoppelSelectionCounts:
    selected: int
    visible: int
    hidden_selected: int
    non_selectable: int


@dataclass(frozen=True)
class MeekoppelPreviewSelectionModel:
    task_rows: tuple[MeekoppelPreviewTaskRow, ...]
    session_checked: frozenset[str]
    anchor: MeekoppelAnchor = "later"
    visibility_filter: VisibilityFilter = "all"
    row_filter_text: str = ""

    @classmethod
    def from_task_rows(
        cls,
        rows: tuple[MeekoppelPreviewTaskRow, ...],
        *,
        anchor: MeekoppelAnchor = "later",
    ) -> MeekoppelPreviewSelectionModel:
        selectable = frozenset(row.pm_id for row in rows if is_shiftable(row))
        model = cls(task_rows=rows, session_checked=selectable, anchor=anchor)
        return model.with_live_rows()

    def with_live_rows(self) -> MeekoppelPreviewSelectionModel:
        rows = recompute_task_rows_for_selection(
            all_rows=self.task_rows,
            checked_pm_ids=self.session_checked,
            anchor=self.anchor,
        )
        if rows == self.task_rows:
            return self
        return replace(self, task_rows=rows)

    def determined_by_line(self) -> str:
        return live_determined_by_line(self.task_rows, self.session_checked)

    def target_year(self) -> int:
        return live_target_year(self.task_rows, self.session_checked)

    def with_visibility_filter(
        self, visibility_filter: VisibilityFilter
    ) -> MeekoppelPreviewSelectionModel:
        if visibility_filter == self.visibility_filter:
            return self
        return replace(self, visibility_filter=visibility_filter)

    def with_row_filter(self, text: str) -> MeekoppelPreviewSelectionModel:
        normalized = text.strip()
        if normalized == self.row_filter_text:
            return self
        return replace(self, row_filter_text=normalized)

    def _matches_row_filter(self, row: MeekoppelPreviewTaskRow) -> bool:
        if not self.row_filter_text:
            return True
        needle = self.row_filter_text.casefold()
        return (
            needle in row.task_label.casefold() or needle in row.pm_id.casefold()
        )

    def visible_rows(self) -> tuple[MeekoppelPreviewTaskRow, ...]:
        return tuple(
            row
            for row in self.task_rows
            if _is_visible(row, self.visibility_filter) and self._matches_row_filter(row)
        )

    def visible_pm_ids(self) -> frozenset[str]:
        return frozenset(row.pm_id for row in self.visible_rows())

    def is_checked(self, pm_id: str) -> bool:
        return pm_id in self.session_checked

    def set_checked(self, pm_id: str, checked: bool) -> MeekoppelPreviewSelectionModel:
        row = next((r for r in self.task_rows if r.pm_id == pm_id), None)
        if row is None or not is_shiftable(row):
            return self
        if checked:
            updated = replace(self, session_checked=self.session_checked | {pm_id})
        else:
            updated = replace(
                self, session_checked=self.session_checked - frozenset({pm_id})
            )
        return updated.with_live_rows()

    def bulk_select_visible(self) -> MeekoppelPreviewSelectionModel:
        add = frozenset(
            row.pm_id for row in self.visible_rows() if is_shiftable(row)
        )
        return replace(
            self, session_checked=self.session_checked | add
        ).with_live_rows()

    def bulk_deselect_visible(self) -> MeekoppelPreviewSelectionModel:
        remove = frozenset(
            row.pm_id for row in self.visible_rows() if is_shiftable(row)
        )
        return replace(
            self, session_checked=self.session_checked - remove
        ).with_live_rows()

    def apply_eligible_pm_ids(self) -> frozenset[str]:
        shiftable = frozenset(row.pm_id for row in self.task_rows if is_shiftable(row))
        return self.session_checked & shiftable

    def selection_counts(self) -> MeekoppelSelectionCounts:
        eligible = self.apply_eligible_pm_ids()
        visible_ids = self.visible_pm_ids()
        hidden_selected = sum(
            1 for pm_id in eligible if pm_id not in visible_ids
        )
        non_selectable = sum(1 for row in self.task_rows if not is_shiftable(row))
        return MeekoppelSelectionCounts(
            selected=len(eligible),
            visible=len(self.visible_rows()),
            hidden_selected=hidden_selected,
            non_selectable=non_selectable,
        )

    def summary_line(self) -> str:
        counts = self.selection_counts()
        return messages.WORKSPACE_MEEKOPPEL_PREVIEW_SELECTION_SUMMARY.format(
            selected=counts.selected,
            visible=counts.visible,
            hidden=counts.hidden_selected,
            non_selectable=counts.non_selectable,
        )

    def apply_enabled(self) -> bool:
        return len(self.apply_eligible_pm_ids()) >= 2
