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


def test_default_selects_all_non_blocked_tasks() -> None:
    rows = (_row("PM-A"), _row("PM-B", delta=0), _row("PM-C", blocked="wettelijk"))
    model = MeekoppelPreviewSelectionModel.from_task_rows(rows)
    assert model.apply_eligible_pm_ids() == frozenset({"PM-A", "PM-B"})
    assert is_shiftable(rows[0])
    assert is_shiftable(rows[1])
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
    rows = (_row("PM-A"), _row("PM-B"), _row("PM-C", blocked="fixed"))
    model = MeekoppelPreviewSelectionModel.from_task_rows(rows)
    model = model.set_checked("PM-B", False)
    narrowed = model.with_visibility_filter("shifting_only")
    assert narrowed.is_checked("PM-B") is False
    assert narrowed.apply_eligible_pm_ids() == frozenset({"PM-A"})
    restored = narrowed.with_visibility_filter("all")
    assert restored.is_checked("PM-B") is False
    assert restored.is_checked("PM-A") is True


def test_summary_counts_selected_visible_hidden_and_non_selectable() -> None:
    rows = (_row("PM-A"), _row("PM-B"), _row("PM-C"), _row("PM-D", blocked="x"))
    model = MeekoppelPreviewSelectionModel.from_task_rows(rows)
    model = (
        model.set_checked("PM-B", False)
        .set_checked("PM-C", False)
        .with_row_filter("PM-A")
    )
    counts = model.selection_counts()
    assert counts.selected == 1
    assert counts.visible == 1
    assert counts.hidden_selected == 0
    assert counts.non_selectable == 1

    model = model.set_checked("PM-B", True)
    counts = model.selection_counts()
    assert counts.selected == 2
    assert counts.hidden_selected == 1

    assert model.summary_line()


def test_live_target_recomputes_when_selection_narrows() -> None:
    rows = (
        MeekoppelPreviewTaskRow(
            pm_id="PM-A",
            task_label="PM-A",
            baseline_year=10,
            effective_year=10,
            target_year=13,
            delta_years=3,
            is_target_driver=False,
            blocked_reason=None,
        ),
        MeekoppelPreviewTaskRow(
            pm_id="PM-B",
            task_label="PM-B",
            baseline_year=11,
            effective_year=11,
            target_year=13,
            delta_years=2,
            is_target_driver=False,
            blocked_reason=None,
        ),
        MeekoppelPreviewTaskRow(
            pm_id="PM-C",
            task_label="PM-C",
            baseline_year=13,
            effective_year=13,
            target_year=13,
            delta_years=0,
            is_target_driver=True,
            blocked_reason=None,
        ),
    )
    model = MeekoppelPreviewSelectionModel.from_task_rows(rows, anchor="later")
    assert model.target_year() == 13

    model = model.set_checked("PM-C", False)
    assert model.target_year() == 11
    pm_a = next(r for r in model.task_rows if r.pm_id == "PM-A")
    pm_b = next(r for r in model.task_rows if r.pm_id == "PM-B")
    pm_c = next(r for r in model.task_rows if r.pm_id == "PM-C")
    assert pm_a.delta_years == 1
    assert pm_b.delta_years == 0
    assert pm_c.delta_years == 0

    model = model.set_checked("PM-A", False)
    assert model.target_year() == 0
    assert model.apply_enabled() is False


def test_live_target_earlier_anchor_uses_minimum() -> None:
    rows = (
        MeekoppelPreviewTaskRow(
            pm_id="PM-A",
            task_label="PM-A",
            baseline_year=10,
            effective_year=10,
            target_year=12,
            delta_years=2,
            is_target_driver=False,
            blocked_reason=None,
        ),
        MeekoppelPreviewTaskRow(
            pm_id="PM-B",
            task_label="PM-B",
            baseline_year=8,
            effective_year=8,
            target_year=12,
            delta_years=4,
            is_target_driver=False,
            blocked_reason=None,
        ),
    )
    model = MeekoppelPreviewSelectionModel.from_task_rows(rows, anchor="earlier")
    assert model.target_year() == 8
