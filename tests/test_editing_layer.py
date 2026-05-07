"""Tests voor de modulaire Streamlit editing layer."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.editing.persistence import build_project_from_state
from rcm_core.editing.state import merge_rows_by_key, parse_bulk_text_for_entity
from rcm_core.editing.validation import validate_entity_rows
from rcm_core.persistence import load_project


def _fixture_project():
    fixture = Path(__file__).parent / "fixtures" / "sample_project.rcm.json"
    return load_project(fixture)


def test_validate_entity_rows_required_and_type_checks():
    project = _fixture_project()
    rows = [
        {
            "fm_id": "",
            "pbs_id": "PBS-001",
            "failure_type": "RANDOM",
            "mttf_jaar": "abc",
        }
    ]
    coerced, errors = validate_entity_rows("faalwijzes", rows, project, edit_current={"faalwijzes": rows})
    assert len(coerced) == 1
    assert "row-1" in errors
    assert "fm_id" in errors["row-1"]
    assert errors["row-1"]["fm_id"][0]["code"] == "REQUIRED_FIELD"
    assert errors["row-1"]["mttf_jaar"][0]["code"] == "TYPE_CHECK"


def test_validate_entity_rows_fk_check_for_pm_task():
    project = _fixture_project()
    rows = [
        {
            "pm_id": "PM-X",
            "fm_id": "FM-DOES-NOT-EXIST",
            "taak_type": "INS",
            "interval_jaar": 1.0,
        }
    ]
    _, errors = validate_entity_rows("pm_tasks", rows, project, edit_current={"pm_tasks": rows})
    assert errors["PM-X"]["fm_id"][0]["code"] == "PM_FM_FK"


def test_bulk_parse_and_merge_pipeline_upserts_rows():
    text = "pm_id\tfm_id\ttaak_type\tinterval_jaar\nPM-001\tFM-001\tINS\t2\nPM-NEW\tFM-002\tREV\t4"
    parsed = parse_bulk_text_for_entity("pm_tasks", text)
    assert len(parsed) == 2

    current = [{"pm_id": "PM-001", "fm_id": "FM-001", "taak_type": "INS", "interval_jaar": 1}]
    merged = merge_rows_by_key("pm_tasks", current, parsed)
    by_id = {row["pm_id"]: row for row in merged}
    assert by_id["PM-001"]["interval_jaar"] == "2"
    assert by_id["PM-NEW"]["fm_id"] == "FM-002"


def test_build_project_from_state_applies_entity_updates():
    project = _fixture_project()
    session = {
        "edit_current": {
            "pbs": [],
            "faalwijzes": [
                {
                    "fm_id": "FM-TEST-NEW",
                    "pbs_id": "PBS-001",
                    "functie_id": "",
                    "faalwijze_omschrijving": "Test FM",
                    "failure_type": "random",
                    "mttf_jaar": 10.0,
                    "sigma_jaar": 1.0,
                    "repair_quality": 1.0,
                    "is_evident": False,
                    "p_ongewenste_gebeurtenis": 0.0,
                    "cost_cm_eur": 0.0,
                    "library_ref": "",
                }
            ],
            "pm_tasks": [],
            "effect_klassen": [],
        }
    }
    built = build_project_from_state(project, session=session)
    assert "FM-TEST-NEW" in built.faalwijzes

