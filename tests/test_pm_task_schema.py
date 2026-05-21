"""PMTask-schema — slice 24 issue 03."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.models import PMTask, TaskType


def test_from_dict_rev_defaults_aging_effect_pct_to_100():
    task = PMTask.from_dict(
        {
            "pm_id": "PM-REV",
            "fm_id": "FM-001",
            "taak_type": "REV",
            "interval_jaar": 5.0,
        }
    )
    assert task.aging_effect_pct == 100.0
    assert task.is_wettelijk_verplicht is False


def test_from_dict_non_rev_defaults_new_fields_to_zero_and_false():
    task = PMTask.from_dict(
        {
            "pm_id": "PM-IN",
            "fm_id": "FM-001",
            "taak_type": "IN",
            "interval_jaar": 1.0,
        }
    )
    assert task.aging_effect_pct == 0.0
    assert task.is_wettelijk_verplicht is False


def test_pm_task_round_trip_includes_new_fields():
    original = PMTask(
        pm_id="PM-X",
        fm_id="FM-001",
        taak_type=TaskType.REV,
        is_wettelijk_verplicht=True,
        aging_effect_pct=75.0,
    )
    restored = PMTask.from_dict(original.to_dict())
    assert restored.is_wettelijk_verplicht is True
    assert restored.aging_effect_pct == 75.0
    assert restored.pm_id == original.pm_id
