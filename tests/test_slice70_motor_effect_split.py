"""Slice 70 issue 02 — CM/PM split effectbijdragen op FMResult."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from rcm_core.engine import compute_fm_result
from rcm_core.models import FMEffectLink, PMEffectLink, RCMProject

SAMPLE = Path("tests/fixtures/sample_project.rcm.json")


@pytest.fixture
def sample_project() -> RCMProject:
    raw = json.loads(SAMPLE.read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def test_fm_result_splits_cm_and_pm_effect_bijdragen(sample_project: RCMProject) -> None:
    """CM = incidenten-equivalent; PM = uren; effect_bijdragen = deprecated mixed som."""
    project = sample_project
    fm = project.faalwijzes["FM-001"]
    pbs = project.pbs_items[fm.pbs_id]
    pm_tasks = [t for t in project.pm_tasks.values() if t.fm_id == fm.fm_id]
    fm_link = FMEffectLink("EL-1", fm.fm_id, "EK-001", fractie=0.5)
    pm_link = PMEffectLink("PL-1", pm_tasks[0].pm_id, "EK-002", fractie=1.0)

    result = compute_fm_result(
        fm,
        pbs,
        pm_tasks,
        project.task_groups,
        project.config,
        fm_effect_links=[fm_link],
        pm_effect_links=[pm_link],
        all_pbs=project.pbs_items,
    )

    assert result.fm_effect_bijdragen == {"EK-001": pytest.approx(result.expected_failures * 0.5)}
    assert "EK-002" in result.pm_effect_bijdragen
    assert result.pm_effect_bijdragen["EK-002"] > 0.0
    mixed = result.effect_bijdragen.get("EK-001", 0.0) + result.effect_bijdragen.get("EK-002", 0.0)
    assert mixed == pytest.approx(
        result.fm_effect_bijdragen.get("EK-001", 0.0) + result.pm_effect_bijdragen.get("EK-002", 0.0)
    )


def test_effect_bijdragen_per_jaar_split_reconciles_lifecycle(sample_project: RCMProject) -> None:
    project = sample_project
    fm = project.faalwijzes["FM-001"]
    pbs = project.pbs_items[fm.pbs_id]
    pm_tasks = [t for t in project.pm_tasks.values() if t.fm_id == fm.fm_id]
    fm_link = FMEffectLink("EL-1", fm.fm_id, "EK-001", fractie=0.5)

    result = compute_fm_result(
        fm,
        pbs,
        pm_tasks,
        project.task_groups,
        project.config,
        fm_effect_links=[fm_link],
        all_pbs=project.pbs_items,
    )

    fm_series = result.fm_effect_bijdragen_per_jaar["EK-001"]
    assert math.isclose(
        sum(fm_series),
        result.fm_effect_bijdragen["EK-001"],
        rel_tol=0,
        abs_tol=1e-3,
    )
    # deprecated mixed bucket ≈ fm + pm per klasse
    mixed_series = result.effect_bijdragen_per_jaar.get("EK-001")
    assert mixed_series is not None
    assert math.isclose(sum(mixed_series), result.effect_bijdragen.get("EK-001", 0.0), abs_tol=1e-3)


def test_fm_result_from_dict_backward_compat_without_split_fields() -> None:
    from rcm_core.models import FMResult

    legacy = {
        "fm_id": "FM-1",
        "pbs_id": "PBS-1",
        "p_failure_lifecycle": 0.5,
        "expected_failures": 2.0,
        "expected_raw_downtime_hr": 10.0,
        "expected_detection_delay_hr": 0.0,
        "expected_total_downtime_hr": 10.0,
        "expected_pm_downtime_hr": 1.0,
        "expected_cm_cost_eur": 100.0,
        "pm_cost_eur": 50.0,
        "total_cost_eur": 150.0,
        "risk_contribution": 0.1,
        "effect_bijdragen": {"EK-1": 3.5},
    }
    fmr = FMResult.from_dict(legacy)
    assert fmr.effect_bijdragen == {"EK-1": 3.5}
    assert fmr.fm_effect_bijdragen == {}
    assert fmr.pm_effect_bijdragen == {}
