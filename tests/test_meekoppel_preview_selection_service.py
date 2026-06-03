"""Unit tests — meekoppel preview selection model (slice 54 issue 04)."""

from __future__ import annotations

from rcm_desktop.adapter.meekoppel_bundle_insight_service import MeekoppelPreviewTaskRow
from rcm_desktop.adapter.meekoppel_preview_selection_service import (
    MeekoppelPreviewSelectionModel,
    is_shiftable,
)


def _row(
    pm_id: str,
    *,
    delta: int = 3,
    blocked: str | None = None,
) -> MeekoppelPreviewTaskRow:
    return MeekoppelPreviewTaskRow(
        pm_id=pm_id,
        task_label=pm_id,
        baseline_year=10,
        effective_year=10,
        target_year=13,
        delta_years=delta,
        is_target_driver=False,
        blocked_reason=blocked,
    )


def test_default_selects_all_shiftable_tasks() -> None:
    rows = (_row("PM-A"), _row("PM-B", delta=0), _row("PM-C", blocked="wettelijk"))
    model = MeekoppelPreviewSelectionModel.from_task_rows(rows)
    assert model.apply_eligible_pm_ids() == frozenset({"PM-A"})
    assert is_shiftable(rows[0])
    assert not is_shiftable(rows[1])
    assert not is_shiftable(rows[2])


def test_bulk_deselect_visible_leaves_hidden_selection() -> None:
    rows = (_row("PM-A"), _row("PM-B"), _row("PM-C"))
    model = MeekoppelPreviewSelectionModel.from_task_rows(rows)
    model = model.with_row_filter("PM-A")
    assert model.visible_pm_ids() == frozenset({"PM-A"})

    model = model.bulk_deselect_visible()
    assert model.apply_eligible_pm_ids() == frozenset({"PM-B", "PM-C"})

    model = model.with_row_filter("")
    assert model.apply_eligible_pm_ids() == frozenset({"PM-B", "PM-C"})


def test_bulk_select_visible_only_checks_visible_shiftable() -> None:
    rows = (_row("PM-A"), _row("PM-B"), _row("PM-C"))
    model = MeekoppelPreviewSelectionModel.from_task_rows(rows)
    model = model.bulk_deselect_visible().with_row_filter("PM-A")
    model = model.bulk_select_visible()
    assert model.apply_eligible_pm_ids() == frozenset({"PM-A"})


def test_filter_change_preserves_session_selection() -> None:
    rows = (_row("PM-A"), _row("PM-B"), _row("PM-C", delta=0))
    model = MeekoppelPreviewSelectionModel.from_task_rows(rows)
    model = model.set_checked("PM-B", False).set_checked("PM-C", True)
    narrowed = model.with_visibility_filter("shifting_only")
    assert narrowed.is_checked("PM-B") is False
    assert narrowed.apply_eligible_pm_ids() == frozenset({"PM-A"})
    restored = narrowed.with_visibility_filter("all")
    assert restored.is_checked("PM-B") is False
    assert restored.is_checked("PM-A") is True


def test_summary_counts_selected_visible_hidden_and_non_selectable() -> None:
    rows = (_row("PM-A"), _row("PM-B"), _row("PM-C", delta=0), _row("PM-D", blocked="x"))
    model = MeekoppelPreviewSelectionModel.from_task_rows(rows)
    model = model.set_checked("PM-B", False).with_row_filter("PM-A")
    counts = model.selection_counts()
    assert counts.selected == 1
    assert counts.visible == 1
    assert counts.hidden_selected == 0
    assert counts.non_selectable == 2

    model = model.set_checked("PM-B", True)
    counts = model.selection_counts()
    assert counts.selected == 2
    assert counts.hidden_selected == 1

    assert model.summary_line()
