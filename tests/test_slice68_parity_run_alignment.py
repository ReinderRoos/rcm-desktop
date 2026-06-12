"""Slice 68 — run-pad CM-overlay alignment + validatie-export regressie."""

from __future__ import annotations

import statistics
from pathlib import Path

import pytest

from rcm_core.failure_parity_validation import build_failure_validation_report
from rcm_core.persistence import load_project
from rcm_desktop.adapter import run_service
from rcm_desktop.adapter.failure_validation_export_service import allocate_validation_causes
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState

GAARKEUKEN = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_Gaarkeuken.rcm.json"
_SCENARIO_DELTA_THRESHOLD = 0.01
_CM_OVERLAY_ACTION = "Run met CM-overlay materialiseren"


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_run_service_default_materializes_import_disabled_pm(monkeypatch) -> None:
    """Zonder planning_overlay: aw_disabled_pm_ids uit import moeten uit run-project."""
    project = load_project(GAARKEUKEN)
    import_disabled = frozenset(
        str(x) for x in (project.import_settings or {}).get("aw_disabled_pm_ids") or []
    )
    assert import_disabled, "Gaarkeuken verwacht CM-overlay PM's uit import"
    sample_pm = next(iter(import_disabled))
    captured: dict[str, object] = {}

    def fake_run(project_arg, project_path_arg, **kwargs):
        captured["project"] = project_arg
        captured["kwargs"] = kwargs
        from rcm_core.engine import run_analytical

        fm_results, pbs_results = run_analytical(project_arg, parallel=False)
        from rcm_core.incremental_run import IncrementalRunResult

        return IncrementalRunResult(
            fm_results={fr.fm_id: fr for fr in fm_results},
            pbs_results=pbs_results,
            cache_only=False,
            affected_fm_ids=[],
            recalculated_fm_count=len(fm_results),
            parallel_retried_sequential=False,
        )

    monkeypatch.setattr(run_service, "run_incremental_analysis", fake_run)

    run_service.run(project, GAARKEUKEN, full_recompute=True)

    run_project = captured["project"]
    assert sample_pm not in run_project.pm_tasks  # type: ignore[union-attr]
    assert sample_pm in project.pm_tasks


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_run_service_active_what_if_overlay_overrides_import_default(monkeypatch) -> None:
    """Actieve what-if overlay zonder disabled PM's: geen import-CM-overlay (analist keuze)."""
    project = load_project(GAARKEUKEN)
    import_disabled = next(
        iter(
            frozenset(
                str(x) for x in (project.import_settings or {}).get("aw_disabled_pm_ids") or []
            )
        )
    )
    overlay = PlanningOverlayState(active=True, anchor_years=(), disabled_pm_ids=frozenset())
    captured: dict[str, object] = {}

    def fake_run(project_arg, project_path_arg, **kwargs):
        captured["project"] = project_arg
        from rcm_core.incremental_run import IncrementalRunResult

        return IncrementalRunResult(
            fm_results={},
            pbs_results={},
            cache_only=False,
            affected_fm_ids=[],
            recalculated_fm_count=0,
            parallel_retried_sequential=False,
        )

    monkeypatch.setattr(run_service, "run_incremental_analysis", fake_run)

    run_service.run(project, GAARKEUKEN, planning_overlay=overlay)

    run_project = captured["project"]
    assert import_disabled in run_project.pm_tasks  # type: ignore[union-attr]


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_run_service_custom_overlay_disabled_set_used(monkeypatch) -> None:
    """Actieve overlay met eigen disabled set overschrijft import-default."""
    project = load_project(GAARKEUKEN)
    if not project.pm_tasks:
        pytest.skip("geen PM-taken")
    custom_pm = next(iter(project.pm_tasks))
    overlay = PlanningOverlayState(
        active=True,
        anchor_years=(),
        disabled_pm_ids=frozenset({custom_pm}),
    )
    captured: dict[str, object] = {}

    def fake_run(project_arg, project_path_arg, **kwargs):
        captured["project"] = project_arg
        from rcm_core.incremental_run import IncrementalRunResult

        return IncrementalRunResult(
            fm_results={},
            pbs_results={},
            cache_only=False,
            affected_fm_ids=[],
            recalculated_fm_count=0,
            parallel_retried_sequential=False,
        )

    monkeypatch.setattr(run_service, "run_incremental_analysis", fake_run)

    run_service.run(project, GAARKEUKEN, planning_overlay=overlay)

    run_project = captured["project"]
    assert custom_pm not in run_project.pm_tasks  # type: ignore[union-attr]


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_run_service_validation_report_no_cm_overlay_action() -> None:
    """E2E: run_service → validation report heeft geen C1-actie (Δ scenario ≈ 0)."""
    project = load_project(GAARKEUKEN)
    result = run_service.run(project, GAARKEUKEN, full_recompute=True)
    assert result.status == "done"
    fm_by_id = {fr.fm_id: fr for fr in result.fm_core_results}
    report = build_failure_validation_report(project, fm_by_id)

    overlay_rows = [r for r in report.rows if r.cm_overlay_disabled_pm_count > 0]
    assert overlay_rows
    deltas = [abs(r.delta_scenario or 0.0) for r in overlay_rows]
    assert statistics.median(deltas) < _SCENARIO_DELTA_THRESHOLD

    c1_actions = [
        r.fm_id
        for r in report.rows
        if _CM_OVERLAY_ACTION in allocate_validation_causes(r).action
    ]
    assert c1_actions == []


SLICE68_DIR = Path(__file__).resolve().parents[1] / ".scratch/rcm-desktop-slice68-parity-run-alignment"
KANBAN_HANDOFF = SLICE68_DIR / "KANBAN_HANDOFF.md"


def test_slice68_kanban_handoff_documents_playbook() -> None:
    assert KANBAN_HANDOFF.is_file(), "KANBAN_HANDOFF.md must exist (issue 05)"
    text = KANBAN_HANDOFF.read_text(encoding="utf-8")
    assert "test_slice68_parity_run_alignment" in text
    assert "run_service" in text
    assert "C1" in text
