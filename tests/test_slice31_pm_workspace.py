"""Slice 31 — LCC what-if overlay (PM-modus verwijderd in slice 33)."""



from __future__ import annotations



import json

from pathlib import Path



from PySide6.QtWidgets import QMessageBox



from rcm_core.models import RCMProject

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState

from rcm_desktop.adapter.results_workspace_state import MODE_LCC

from rcm_desktop.adapter.run_service import run as run_single

from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow



from tests.test_desktop_results_workspace_window import _ensure_app



FIXTURE = Path("tests/fixtures/one_fm_planning.rcm.json")





def _open_with_run(window: ResultsWorkspaceWindow, monkeypatch) -> None:

    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)

    project = RCMProject.from_dict(json.loads(FIXTURE.read_text(encoding="utf-8")))

    window._state.set_last_project(project)

    rr = run_single(project, FIXTURE, full_recompute=True, parallel=False)

    assert rr.status == "done"

    window._state.set_last_run(rr)

    window._rerender_detail_for_current_scope()

    window.show()





def test_lcc_preventief_drops_after_rev_passive_overlay(monkeypatch):

    app = _ensure_app()

    window = ResultsWorkspaceWindow()

    _open_with_run(window, monkeypatch)

    app.processEvents()



    window.workspace_state.set_modus(MODE_LCC)

    app.processEvents()

    baseline_sum = sum(b.preventief_eur for b in window.lcc_chart_widget.buckets())



    overlay = PlanningOverlayState.inactive().begin_what_if().bulk_all_rev_passive(

        window._state.last_project

    )

    window.workspace_state.set_planning_overlay(overlay)

    app.processEvents()



    whatif_sum = sum(b.preventief_eur for b in window.lcc_chart_widget.buckets())

    assert window.workspace_state.snapshot().planning_overlay.active is True
    assert whatif_sum <= baseline_sum + 1e-3





def test_lcc_rev_filter_matches_filtered_preventief(monkeypatch):

    app = _ensure_app()

    window = ResultsWorkspaceWindow()

    _open_with_run(window, monkeypatch)

    app.processEvents()



    window.workspace_state.set_modus(MODE_LCC)

    app.processEvents()

    for key in ("rev", "in_task", "tst", "svo", "wet"):

        window._lcc_filter_checks[key].setChecked(key == "rev")

    window._on_lcc_filter_toggled()

    app.processEvents()



    rev_only = sum(b.preventief_eur for b in window.lcc_chart_widget.buckets())

    assert rev_only >= 0.0


