"""Integratie — CM vs PM LCC-divergentie (slice 24 issue 04)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.engine import compute_fm_result
from rcm_core.lcc_profile import build_cm_eur_per_bucket
from rcm_core.models import PMTask, TaskType
from rcm_core.persistence import load_project
from rcm_core.scenarios import SCENARIO_CM, SCENARIO_PM
from rcm_core.units import TimeDuration, TimeUnit
from rcm_desktop.adapter.scenario_run_service import build_project_for_scenario


def _fm_results(project):
    out = []
    for fm in project.faalwijzes.values():
        pbs = project.pbs_items.get(fm.pbs_id)
        if pbs is None:
            continue
        out.append(
            compute_fm_result(
                fm,
                pbs,
                [t for t in project.pm_tasks.values() if t.fm_id == fm.fm_id],
                project.task_groups,
                project.config,
                all_pbs=project.pbs_items,
            )
        )
    return out


def test_cm_vs_pm_lcc_curves_diverge_on_demo_fixture():
    path = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(path)
    project.pm_tasks["PM-REV"] = PMTask(
        pm_id="PM-REV",
        fm_id="FM-001",
        taak_type=TaskType.REV,
        taak_omschrijving="Revisie",
        interval_jaar=5.0,
        duration=TimeDuration(24.0, TimeUnit.HOURS),
        cost_eur=5000.0,
    )
    cm_project = build_project_for_scenario(project, SCENARIO_CM)
    pm_project = build_project_for_scenario(project, SCENARIO_PM)

    cm_frs = _fm_results(cm_project)
    pm_frs = _fm_results(pm_project)
    cm_curve = build_cm_eur_per_bucket(cm_project, cm_frs)
    pm_curve = build_cm_eur_per_bucket(pm_project, pm_frs)

    assert sum(cm_curve) > 0.0 and sum(pm_curve) > 0.0
    assert len(cm_project.pm_tasks) < len(pm_project.pm_tasks)
    fm001_cm = next(fr for fr in cm_frs if fr.fm_id == "FM-001")
    fm001_pm = next(fr for fr in pm_frs if fr.fm_id == "FM-001")
    assert fm001_cm.pm_cost_eur != fm001_pm.pm_cost_eur
