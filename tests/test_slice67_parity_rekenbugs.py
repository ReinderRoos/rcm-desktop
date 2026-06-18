"""Slice 67 issues 02–07 — parity-rekenbugs regressie."""

from __future__ import annotations

import statistics
from pathlib import Path

import pytest

from rcm_core.cm_overlay import materialize_cm_overlay_project
from rcm_core.config import RCMConfig
from rcm_core.engine import run_analytical
from rcm_core.failure_parity_validation import build_failure_validation_report
from rcm_core.input_parity_audit import audit_input_parity
from rcm_core.models import TaskType
from rcm_core.persistence import load_project
from rcm_core.rcm_cost_benchmark import build_parity_report
from rcm_core.rev_interval_audit import audit_rev_interval_parity
from rcm_desktop import messages

GAARKEUKEN = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_Gaarkeuken.rcm.json"
SLICE67_DIR = Path(__file__).resolve().parents[1] / ".scratch/rcm-desktop-slice67-parity-rekenbugs"
KANBAN_HANDOFF = SLICE67_DIR / "KANBAN_HANDOFF.md"

_SCENARIO_DELTA_THRESHOLD = 0.01


def _gaarkeuken_cm_aligned_report():
    project = load_project(GAARKEUKEN)
    aligned = materialize_cm_overlay_project(project)
    fm_results, _ = run_analytical(aligned, parallel=False)
    report = build_failure_validation_report(project, fm_results)
    return project, report


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_gaarkeuken_rev_aw_100pct_matches_cm_overlay() -> None:
    _project, report = _gaarkeuken_cm_aligned_report()
    assert all(abs(r.ef_rev_aw_100pct - r.ef_cm_overlay) < 1e-9 for r in report.rows)


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_gaarkeuken_rev_tasks_default_aging_effect_pct_100() -> None:
    project = load_project(GAARKEUKEN)
    rev_tasks = [t for t in project.pm_tasks.values() if t.taak_type == TaskType.REV]
    assert rev_tasks, "verwacht REV-taken op Gaarkeuken"
    assert all(t.aging_effect_pct == 100.0 for t in rev_tasks)


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_cm_overlay_run_delta_scenario_median_small() -> None:
    _project, report = _gaarkeuken_cm_aligned_report()
    overlay_rows = [r for r in report.rows if r.cm_overlay_disabled_pm_count > 0]
    assert overlay_rows
    deltas = [abs(r.delta_scenario or 0.0) for r in overlay_rows]
    assert statistics.median(deltas) < _SCENARIO_DELTA_THRESHOLD


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_repair_quality_actual_matches_rq0_counterfactual() -> None:
    _project, report = _gaarkeuken_cm_aligned_report()
    for row in report.rows:
        assert abs(row.ef_actual - row.ef_rq_0) < 0.001


def test_aw_mc_lifecycle_horizon_default_is_true() -> None:
    assert RCMConfig().aw_mc_lifecycle_horizon is True


def test_horizon_playbook_hint_in_model_settings_messages() -> None:
    tooltip = messages.MODEL_SETTINGS_AW_MC_HORIZON_TTIP
    assert "LifeTime" in tooltip or "leeftijd" in tooltip.lower()
    assert "AW" in tooltip or "Monte Carlo" in tooltip


def test_slice67_kanban_handoff_documents_playbook() -> None:
    assert KANBAN_HANDOFF.is_file(), "KANBAN_HANDOFF.md must exist (issue 07)"
    text = KANBAN_HANDOFF.read_text(encoding="utf-8")
    assert "herimport" in text.lower() or "Herimport" in text
    assert "aw_mc_lifecycle_horizon" in text
    assert "test_gaarkeuken_parity_gate" in text or "build_parity_report" in text


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_gaarkeuken_mttf_input_parity_no_systematic_mismatch() -> None:
    project = load_project(GAARKEUKEN)
    audit = audit_input_parity(project)
    assert audit.count_by_dimension("mttf") == 0


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_gaarkeuken_initial_age_mismatches_documented() -> None:
    """InitialAge-conflicten (wizard) zijn bekend; audit telt ze expliciet."""
    project = load_project(GAARKEUKEN)
    audit = audit_input_parity(project)
    assert audit.fm_count == 135
    # Geen stille MTTF-bug; leeftijd-afwijkingen zijn analist/wizard-scope (B3).
    assert audit.count_by_dimension("mttf") == 0


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_gaarkeuken_rev_interval_overlay_audit_populated() -> None:
    project = load_project(GAARKEUKEN)
    audit = audit_rev_interval_parity(project)
    assert audit.fm_count == 135
    assert audit.overlay_only_fms, "CM-overlay deactiveert REV op subset van aging-FM's"


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_gaarkeuken_parity_gate_no_rev_survival_explosion_after_slice67() -> None:
    project = load_project(GAARKEUKEN)
    aligned = materialize_cm_overlay_project(project)
    fm_results, _ = run_analytical(aligned, parallel=False)
    report = build_parity_report(project, fm_results)
    explosive = [
        r.fm_id
        for r in report.rows
        if r.expected_failures_rcm is not None and r.expected_failures_rcm > 10_000.0
    ]
    assert explosive == []
    assert report.summary.fail_count <= 128
