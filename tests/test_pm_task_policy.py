"""PM task policy — shiftability and wettelijk labeling (adapter SSOT)."""

from __future__ import annotations

from rcm_core.models import PMTask, TaskType

from rcm_desktop.adapter.pm_task_policy import (
    is_pm_shiftable,
    is_pm_wettelijk,
    is_pm_wettelijk_from_import_fields,
    pm_shift_block_reason,
)


def test_rev_task_without_wet_markers_is_shiftable():
    task = PMTask(
        pm_id="PM-REV",
        fm_id="FM-1",
        taak_type=TaskType.REV,
        taak_omschrijving="Revisie pomp",
        interval_jaar=5.0,
    )
    assert is_pm_shiftable(task) is True
    assert is_pm_wettelijk(task) is False
    assert pm_shift_block_reason(task) is None


def test_svo_task_is_not_shiftable():
    task = PMTask(
        pm_id="PM-SVO",
        fm_id="FM-1",
        taak_type=TaskType.SVO,
        interval_jaar=1.0,
    )
    assert is_pm_shiftable(task) is False
    assert pm_shift_block_reason(task) is not None
    assert "SVO" in pm_shift_block_reason(task)


def test_wettelijk_task_is_not_shiftable():
    task = PMTask(
        pm_id="PM-WET",
        fm_id="FM-1",
        taak_type=TaskType.IN,
        taak_omschrijving="WET inspectie",
        interval_jaar=1.0,
    )
    assert is_pm_wettelijk(task) is True
    assert is_pm_shiftable(task) is False
    assert pm_shift_block_reason(task) is not None


def test_is_wettelijk_verplicht_flag_blocks_shift_without_wet_in_description():
    task = PMTask(
        pm_id="PM-FLAG",
        fm_id="FM-1",
        taak_type=TaskType.REV,
        taak_omschrijving="Periodieke revisie",
        interval_jaar=5.0,
        is_wettelijk_verplicht=True,
    )
    assert is_pm_wettelijk(task) is True
    assert is_pm_shiftable(task) is False


def test_import_wettelijk_detection_matches_aw_fields():
    assert is_pm_wettelijk_from_import_fields(
        aw_type="Inspection",
        task_id="PM-WET-01",
        description="Routine",
    ) is True
    assert is_pm_wettelijk_from_import_fields(
        aw_type="WET",
        task_id="PM-01",
        description="Routine",
    ) is True
    assert is_pm_wettelijk_from_import_fields(
        aw_type="Inspection",
        task_id="PM-01",
        description="WET controle",
    ) is True
    assert is_pm_wettelijk_from_import_fields(
        aw_type="Inspection",
        task_id="PM-01",
        description="Routine",
    ) is False


def test_unknown_task_returns_block_reason():
    assert pm_shift_block_reason(None) == "Onbekende PM-taak."
