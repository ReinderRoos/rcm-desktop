"""Unit tests for PM vs FM effect import rules (issue 02 spike)."""

from __future__ import annotations

from rcm_core.isograph_pm_import_rules import (
    CauseEffectAssignmentRow,
    ScheduledTaskRow,
    fm_effect_fractie,
    pm_effect_fractie,
    pm_import_warning_unresolved,
    resolve_pm_task_id,
    resolve_pm_tasks,
    should_create_fm_effect_link,
    should_create_pm_effect_link,
)


def test_fm_link_only_when_c_enable() -> None:
    row = CauseEffectAssignmentRow(
        cause_id="FM-1",
        effect_id="E1",
        c_enable="True",
        p_enable="False",
        i_enable="False",
        redundancy_factor=0.1,
    )
    assert should_create_fm_effect_link(row)
    assert fm_effect_fractie(row) == 0.1
    assert not should_create_pm_effect_link(row, [])


def test_pm_link_resolves_by_cause_and_subindex() -> None:
    row = CauseEffectAssignmentRow(
        cause_id="FM-1",
        effect_id="E1",
        c_enable="False",
        p_enable="True",
        i_enable="False",
        redundancy_factor=1,
        sub_index=2,
    )
    tasks = [
        ScheduledTaskRow(
            cause_id="FM-1",
            sub_index=2,
            task_id="REV",
            task_type="Planned",
            enabled="True",
        ),
        ScheduledTaskRow(
            cause_id="FM-1",
            sub_index=0,
            task_id="SVO",
            task_type="Planned",
            enabled="True",
        ),
    ]
    assert resolve_pm_task_id(row, tasks) == "REV"


def test_pm_warning_when_no_matching_task() -> None:
    row = CauseEffectAssignmentRow(
        cause_id="FM-1",
        effect_id="E1",
        c_enable="False",
        p_enable="True",
        i_enable="True",
        redundancy_factor=1,
        sub_index=0,
    )
    msg = pm_import_warning_unresolved(row)
    assert msg is not None
    assert "FM-1" in msg


def test_pm_link_resolves_when_scheduled_task_disabled() -> None:
    """Enabled=False is scenario; structurele koppeling blijft."""
    row = CauseEffectAssignmentRow(
        cause_id="FM-1",
        effect_id="E1",
        c_enable="False",
        p_enable="True",
        i_enable="False",
        redundancy_factor=1,
        sub_index=0,
    )
    tasks = [
        ScheduledTaskRow(
            cause_id="FM-1",
            sub_index=0,
            task_id="REV",
            task_type="Planned",
            enabled="False",
        ),
    ]
    assert resolve_pm_task_id(row, tasks) == "REV"
    assert should_create_pm_effect_link(row, tasks)


def test_pm_effect_fractie_matches_assignment_rf() -> None:
    row = CauseEffectAssignmentRow(
        cause_id="FM-1",
        effect_id="E1",
        c_enable="False",
        p_enable="True",
        i_enable="False",
        redundancy_factor=0.5,
    )
    assert pm_effect_fractie(row) == 0.5


def test_dual_scope_returns_two_tasks_when_rev_and_in() -> None:
    row = CauseEffectAssignmentRow(
        cause_id="FM-1",
        effect_id="E1",
        c_enable="False",
        p_enable="True",
        i_enable="True",
        redundancy_factor=1,
        sub_index=0,
    )
    tasks = [
        ScheduledTaskRow("FM-1", 0, "REV", "Planned", "True"),
        ScheduledTaskRow("FM-1", 1, "IN", "Inspection", "True"),
    ]
    resolved, _ = resolve_pm_tasks(row, tasks)
    assert len(resolved) == 2


def test_ambiguous_tasks_return_no_pm_link() -> None:
    row = CauseEffectAssignmentRow(
        cause_id="FM-1",
        effect_id="E1",
        c_enable="False",
        p_enable="True",
        i_enable="False",
        redundancy_factor=1,
        sub_index=0,
    )
    tasks = [
        ScheduledTaskRow("FM-1", 0, "A", "Planned", "True"),
        ScheduledTaskRow("FM-1", 0, "B", "Planned", "True"),
    ]
    assert resolve_pm_task_id(row, tasks) is None
