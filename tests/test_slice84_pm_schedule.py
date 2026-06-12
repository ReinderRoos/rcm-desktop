"""Slice 84 — PM-schedule-helper (issue 01 tracer bullet)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.models import PMTask, TaskType
from rcm_core.persistence import load_project
from rcm_core.pm_schedule import pm_execution_count, pm_execution_years, pm_first_execution_year

from rcm_desktop.adapter.ltap_execution_schedule import ltap_executions_by_year
from rcm_desktop.adapter.ltap_service import build_ltap_view


@pytest.mark.parametrize(
    "interval,lifecycle,anchor,expected_years",
    [
        (5.0, 50.0, 0.0, (0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0)),
        (16.0, 50.0, 0.0, (0.0, 16.0, 32.0, 48.0)),
        (25.0, 50.0, 0.0, (0.0, 25.0)),
        (60.0, 50.0, 0.0, (0.0,)),
        (60.0, 50.0, 55.0, ()),
        (0.0, 50.0, 0.0, ()),
        (-1.0, 50.0, 0.0, ()),
    ],
)
def test_pm_execution_years_table_driven(
    interval: float,
    lifecycle: float,
    anchor: float,
    expected_years: tuple[float, ...],
) -> None:
    assert pm_execution_years(interval, lifecycle_years=lifecycle, anchor_year=anchor) == expected_years
    assert pm_execution_count(interval, lifecycle_years=lifecycle, anchor_year=anchor) == len(expected_years)
    assert pm_first_execution_year(interval, lifecycle_years=lifecycle, anchor_year=anchor) == (
        expected_years[0] if expected_years else None
    )


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def test_pm_schedule_matches_ltap_execution_buckets(sample_project) -> None:
    lifecycle = float(sample_project.config.lifecycle_years)
    for task in sample_project.pm_tasks.values():
        if float(task.interval_jaar) <= 0:
            continue
        by_year = ltap_executions_by_year(task, lifecycle_years=lifecycle, anchor_year=0.0)
        assert pm_execution_count(
            float(task.interval_jaar),
            lifecycle_years=lifecycle,
            anchor_year=0.0,
        ) == sum(by_year.values())


def test_pm_schedule_matches_ltap_view_task_totals(sample_project) -> None:
    lifecycle = float(sample_project.config.lifecycle_years)
    view = build_ltap_view(sample_project)
    totals_by_pm: dict[str, int] = {}
    for row in view.years:
        for detail in row.details:
            totals_by_pm[detail.pm_id] = totals_by_pm.get(detail.pm_id, 0) + detail.executions
    for task in sample_project.pm_tasks.values():
        if float(task.interval_jaar) <= 0:
            continue
        expected = pm_execution_count(
            float(task.interval_jaar),
            lifecycle_years=lifecycle,
            anchor_year=0.0,
        )
        assert totals_by_pm.get(task.pm_id, 0) == expected


def test_rev_tasks_derived_execution_count_matches_helper(sample_project) -> None:
    from rcm_desktop.adapter.entity_grid_derived_values import entity_derived_value

    task = sample_project.pm_tasks["PM-002"]
    lifecycle = float(sample_project.config.lifecycle_years)
    row = {"interval_jaar": float(task.interval_jaar)}
    expected = pm_execution_count(float(task.interval_jaar), lifecycle_years=lifecycle)
    assert (
        entity_derived_value("input.rev_tasks", "pm_execution_count_lcc", sample_project, row)
        == expected
    )


def test_rev_tasks_interval_change_refreshes_derived_columns(sample_project) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt

    from rcm_desktop.adapter.entity_edit_service import EntityEditService
    from rcm_desktop.views.panels.entity_grid_panel import EntityGridPanel

    from tests.test_desktop_results_workspace_window import _ensure_app

    _ensure_app()
    svc = EntityEditService.for_view("input.rev_tasks")
    svc.init(sample_project)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.rev_tasks")
    model = panel.table_model()
    assert model is not None

    count_col = model._columns.index("pm_execution_count_lcc")
    row_idx = next(i for i, r in enumerate(svc.rows()) if r.row_key == "PM-002")
    before = model.data(model.index(row_idx, count_col), Qt.DisplayRole)

    svc.apply_change("PM-002", "interval_jaar", "10")
    model.emit_grid_refresh()
    after = model.data(model.index(row_idx, count_col), Qt.DisplayRole)
    assert before != after


def test_rev_tasks_derived_columns_are_read_only(sample_project) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt

    from rcm_desktop.adapter.entity_edit_service import EntityEditService
    from rcm_desktop.views.panels.entity_grid_panel import EntityGridPanel

    from tests.test_desktop_results_workspace_window import _ensure_app

    _ensure_app()
    svc = EntityEditService.for_view("input.rev_tasks")
    svc.init(sample_project)
    panel = EntityGridPanel()
    panel.attach(svc, sample_project, view_id="input.rev_tasks")
    model = panel.table_model()
    assert model is not None

    row_idx = 0
    for col_id in ("pm_first_execution_year", "pm_execution_count_lcc"):
        col = model._columns.index(col_id)
        flags = model.flags(model.index(row_idx, col))
        assert not (flags & Qt.ItemIsEditable)
        before = model.data(model.index(row_idx, col), Qt.DisplayRole)
        assert model.setData(model.index(row_idx, col), "999", Qt.EditRole) is False
        assert model.data(model.index(row_idx, col), Qt.DisplayRole) == before


def test_rev_tasks_optional_columns_default_hidden() -> None:
    from rcm_desktop.adapter.entity_grid_column_settings import default_hidden_columns

    hidden = default_hidden_columns("input.rev_tasks")
    assert "pm_downtime_oh" in hidden
    assert "pm_repair_quality" in hidden
    assert "pm_herstelduur" in hidden


def test_rev_tasks_downtime_oh_shows_effect_rf(sample_project) -> None:
    from rcm_desktop.adapter.entity_grid_derived_values import entity_derived_value

    task = sample_project.pm_tasks["PM-002"]
    row = dict(task.to_dict())
    display = entity_derived_value("input.rev_tasks", "pm_downtime_oh", sample_project, row)
    assert "EK-SYS-01" in display
    assert "RF=1" in display


def test_rev_tasks_optional_columns_via_column_choice(sample_project, tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt, QSettings

    from rcm_desktop.adapter.entity_edit_service import EntityEditService
    from rcm_desktop.adapter.entity_grid_column_settings import (
        resolve_visible_columns,
        write_hidden_entity_columns,
    )
    from rcm_desktop.views.panels.entity_grid_panel import EntityGridPanel

    from tests.test_desktop_results_workspace_window import _ensure_app

    _ensure_app()
    settings_path = tmp_path / "settings.ini"
    settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
    write_hidden_entity_columns(settings, "input.rev_tasks", frozenset({"pm_id"}))

    visible = resolve_visible_columns(
        "input.rev_tasks",
        frozenset({"pm_id"}),
    )
    assert "pm_downtime_oh" in visible

    svc = EntityEditService.for_view("input.rev_tasks")
    svc.init(sample_project)
    panel = EntityGridPanel()
    panel.attach(
        svc,
        sample_project,
        view_id="input.rev_tasks",
        hidden_columns=frozenset({"pm_id"}),
    )
    model = panel.table_model()
    assert model is not None
    headers = [
        model.headerData(col, Qt.Orientation.Horizontal, Qt.DisplayRole)
        for col in range(model.columnCount())
    ]
    assert "Downtime bij OH" in headers
