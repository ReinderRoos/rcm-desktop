"""Slice 27 issue 05 — jaarlijkse effectklassen op FMResult."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from rcm_core.engine import compute_fm_result
from rcm_core.models import FMEffectLink, RCMProject


@pytest.fixture
def sample_project() -> RCMProject:
    raw = json.loads(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def test_effect_bijdragen_per_jaar_reconciles_lifecycle(sample_project: RCMProject):
    project = sample_project
    link = FMEffectLink(
        link_id="EL-1",
        fm_id="FM-001",
        klasse_id="EK-001",
        fractie=0.5,
    )
    project.fm_effect_links["EL-1"] = link
    fm = project.faalwijzes["FM-001"]
    pbs = project.pbs_items[fm.pbs_id]
    pm_tasks = [t for t in project.pm_tasks.values() if t.fm_id == fm.fm_id]
    result = compute_fm_result(
        fm,
        pbs,
        pm_tasks,
        project.task_groups,
        project.config,
        fm_effect_links=[link],
        all_pbs=project.pbs_items,
    )
    series = result.effect_bijdragen_per_jaar.get("EK-001")
    assert series is not None
    assert math.isclose(
        sum(series),
        result.effect_bijdragen.get("EK-001", 0.0),
        rel_tol=0,
        abs_tol=1e-3,
    )


def test_effect_concentrates_in_peak_faalmoment_year(sample_project: RCMProject):
    project = sample_project
    fm = project.faalwijzes["FM-001"]
    pbs = project.pbs_items[fm.pbs_id]
    pm_tasks = [t for t in project.pm_tasks.values() if t.fm_id == fm.fm_id]
    result = compute_fm_result(
        fm,
        pbs,
        pm_tasks,
        project.task_groups,
        project.config,
        fm_effect_links=[
            FMEffectLink("EL-1", fm.fm_id, "EK-001", fractie=1.0),
        ],
        all_pbs=project.pbs_items,
    )
    series = result.effect_bijdragen_per_jaar["EK-001"]
    peak_h = max(range(len(series)), key=lambda h: series[h])
    assert series[peak_h] > sum(series) * 0.05
