"""Slice 36 issue 05 — horizon_profile bij run tests."""
from __future__ import annotations

import json
import math
from pathlib import Path

from rcm_core.engine import compute_fm_result
from rcm_core.lcc_profile import build_cor_eur_per_bucket
from rcm_core.models import RCMProject


def _sample_project() -> RCMProject:
    raw = json.loads(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def test_compute_fm_result_populates_horizon_profile():
    project = _sample_project()
    fm = next(iter(project.faalwijzes.values()))
    pbs = project.pbs_items[fm.pbs_id]
    pm_tasks = [t for t in project.pm_tasks.values() if t.fm_id == fm.fm_id]
    result = compute_fm_result(
        fm,
        pbs,
        pm_tasks,
        project.task_groups,
        project.config,
        all_pbs=project.pbs_items,
    )
    assert result.horizon_profile is not None
    num = len(result.horizon_profile.cor_eur)
    assert num > 0
    assert math.isclose(
        sum(result.horizon_profile.cor_eur),
        result.expected_cm_cost_eur,
        rel_tol=0,
        abs_tol=1e-3,
    )


def test_fresh_run_skips_legacy_cor_bucket_path():
    project = _sample_project()
    fm_results = []
    for fm in project.faalwijzes.values():
        pbs = project.pbs_items.get(fm.pbs_id)
        if pbs is None:
            continue
        pm_tasks = [t for t in project.pm_tasks.values() if t.fm_id == fm.fm_id]
        fm_results.append(
            compute_fm_result(
                fm,
                pbs,
                pm_tasks,
                project.task_groups,
                project.config,
                all_pbs=project.pbs_items,
            )
        )
    _, used_legacy = build_cor_eur_per_bucket(project, fm_results)
    assert used_legacy is False
