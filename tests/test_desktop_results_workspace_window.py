from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from rcm_core.models import FMHorizonProfile, FMResult
from rcm_core.persistence import load_project
from rcm_desktop import messages
from rcm_desktop.adapter.result_view_service import FMResultRow, PBSResultRow
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    MODE_LCC,
    SOURCE_FAALWIJZE,
    SOURCE_PBS,
)
from rcm_desktop import messages
from rcm_desktop.adapter.run_service import RunMetrics, RunResult, run as run_single
from rcm_desktop.adapter.validate_service import DetailItem, ValidateResult
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _three_level_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def _done_run_for_fixture() -> RunResult:
    project = _three_level_project()
    pbs_ids = list(project.pbs_items)
    fm_core_results = (
        FMResult(
            fm_id="FM-A",
            pbs_id=pbs_ids[0],
            p_failure_lifecycle=0.4,
            expected_failures=4.0,
            expected_raw_downtime_hr=9.5,
            expected_detection_delay_hr=0.5,
            expected_total_downtime_hr=10.0,
            expected_pm_downtime_hr=0.0,
            expected_cm_cost_eur=120.0,
            pm_cost_eur=80.0,
            total_cost_eur=200.0,
            risk_contribution=0.2,
        ),
        FMResult(
            fm_id="FM-B",
            pbs_id=pbs_ids[-1],
            p_failure_lifecycle=0.6,
            expected_failures=6.0,
            expected_raw_downtime_hr=9.5,
            expected_detection_delay_hr=0.5,
            expected_total_downtime_hr=10.0,
            expected_pm_downtime_hr=0.0,
            expected_cm_cost_eur=180.0,
            pm_cost_eur=120.0,
            total_cost_eur=300.0,
            risk_contribution=0.3,
        ),
    )
    return RunResult(
        status="done",
        summary="klaar",
        metrics=RunMetrics(
            fm_result_count=2,
            total_lifecycle_faalmomenten=10.0,
            total_cost_eur=500.0,
            total_downtime_hr=20.0,
            lifecycle_years=float(project.config.lifecycle_years),
            total_risk_contribution=0.5,
        ),
        fm_core_results=fm_core_results,
        rows=[
            FMResultRow(
                fm_id="FM-A",
                faalwijze_omschrijving="omsch A",
                pbs_id=pbs_ids[0],
                bouwdeel_naam=project.pbs_items[pbs_ids[0]].bouwdeel_naam,
                expected_failures=4.0,
                expected_total_downtime_hr=10.0,
                total_cost_eur=200.0,
            ),
            FMResultRow(
                fm_id="FM-B",
                faalwijze_omschrijving="omsch B",
                pbs_id=pbs_ids[-1],
                bouwdeel_naam=project.pbs_items[pbs_ids[-1]].bouwdeel_naam,
                expected_failures=6.0,
                expected_total_downtime_hr=10.0,
                total_cost_eur=300.0,
            ),
        ],
        pbs_rows=[
            PBSResultRow(
                pbs_id=pid,
                bouwdeel_naam=project.pbs_items[pid].bouwdeel_naam,
                parent_pbs_id=(
                    project.pbs_items[pid].parent_pbs_id
                    if project.pbs_items[pid].parent_pbs_id in project.pbs_items
                    else None
                ),
                level=0,
                sort_path=(pid,),
                expected_failures_self=0.0,
                total_downtime_hr_self=0.0,
                total_cost_eur_self=0.0,
                expected_failures_total=10.0 if pid == pbs_ids[0] else 0.0,
                total_downtime_hr_total=10.0 if pid == pbs_ids[0] else 0.0,
                total_cost_eur_total=500.0 if pid == pbs_ids[0] else 0.0,
                unavailability_pct_total=0.5,
            )
            for pid in pbs_ids
        ],
    )


def _inject_run(window: ResultsWorkspaceWindow, project, *, use_fixture_path: bool = True) -> RunResult:
    """Zet last_run via het slice-26 run-pad (zonder achtergrondthread)."""
    from rcm_desktop.adapter.presentation_cache_service import build_project_total_presentation

    path = Path("tests/fixtures/sample_project.rcm.json") if use_fixture_path else window.path_input.text()
    run = run_single(project, path)
    presentation = (
        build_project_total_presentation(project, run) if run.status == "done" else None
    )
    window._on_run_result_ready(run, presentation)
    return run


def test_workspace_window_constructs_with_pbs_sidebar_visible(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.pbs_sidebar.isVisible() is True
    assert window.pbs_toggle_button.isChecked() is True
    assert window.show_whole_project_button is not None
    assert window.pbs_filter_input is not None
    assert window.pbs_tree_view is not None


def test_workspace_window_pbs_toggle_hides_sidebar(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    window.pbs_toggle_button.setChecked(False)
    app.processEvents()
    assert window.pbs_sidebar.isVisible() is False

    window.pbs_toggle_button.setChecked(True)
    app.processEvents()
    assert window.pbs_sidebar.isVisible() is True


def test_workspace_window_renders_pbs_structure_before_run(monkeypatch):
    """Project loaded but no run yet — PBS tree should show structure with `—` cells."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    app.processEvents()

    model = window.pbs_tree_view.model()
    assert model is not None
    assert model.rowCount() >= 1
    # Numeric columns should render the empty placeholder (column 2 = faalmomenten_total)
    first_root_index = model.index(0, 2)
    assert model.data(first_root_index, Qt.DisplayRole) == "—"


def test_workspace_window_renders_pbs_totals_after_run(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    run = _done_run_for_fixture()
    window._state.set_last_run(run)
    app.processEvents()

    model = window.pbs_tree_view.model()
    assert model is not None
    first_root_index = model.index(0, 2)
    rendered = model.data(first_root_index, Qt.DisplayRole)
    assert rendered != "—"


def test_workspace_window_pbs_filter_shows_matching_paths_only(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    app.processEvents()

    first_pbs_id = next(iter(project.pbs_items))
    window.pbs_filter_input.setText(first_pbs_id)
    app.processEvents()

    proxy_model = window.pbs_tree_view.model()
    assert proxy_model is not None
    # At least one row matches; visible rows ≤ total rows in source.
    assert proxy_model.rowCount(QModelIndex()) >= 1


def test_workspace_window_pbs_filter_empty_state_when_no_matches(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    app.processEvents()

    window.pbs_filter_input.setText("ZZZ_NOT_A_MATCH_XYZ")
    app.processEvents()

    proxy_model = window.pbs_tree_view.model()
    assert proxy_model.rowCount(QModelIndex()) == 0
    assert window.pbs_empty_state_label.isVisible() is True


def test_workspace_window_scope_filter_on_fm_table_after_pbs_click(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    run = _done_run_for_fixture()
    window._state.set_last_run(run)
    app.processEvents()

    pbs_ids = list(project.pbs_items)
    last_pbs_id = pbs_ids[-1]

    # Programmatic scope change (the API the UI uses when a tree node is clicked).
    window.set_pbs_scope(last_pbs_id)
    window.modus_buttons["fm_detail"].click()
    app.processEvents()

    fm_model = window.fm_table_view.model()
    assert fm_model is not None
    fm_ids = {
        fm_model.data(fm_model.index(r, 0), Qt.DisplayRole)
        for r in range(fm_model.rowCount())
    }
    assert fm_ids == {"FM-B"}


def test_workspace_window_show_whole_project_resets_scope(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    run = _done_run_for_fixture()
    window._state.set_last_run(run)
    pbs_ids = list(project.pbs_items)
    window.set_pbs_scope(pbs_ids[-1])
    window.modus_buttons["fm_detail"].click()
    app.processEvents()
    assert window.fm_table_view.model().rowCount() == 1

    window.show_whole_project_button.click()
    app.processEvents()

    assert window._pbs_scope_id is None
    fm_model = window.fm_table_view.model()
    assert fm_model.rowCount() == 2


def test_workspace_toolbar_text_has_no_legacy_labels(monkeypatch):
    """Issue 08 — geen "Volledige analyse" of "Vergelijk scenario's"-strings
    meer in zichtbare toolbar-knoppen van de hoofdwerkruimte."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    from PySide6.QtWidgets import QAbstractButton

    button_texts = {
        b.text() for b in window.findChildren(QAbstractButton)
    }
    assert "Volledige analyse" not in button_texts
    assert "Vergelijk scenario's (CM/PM)" not in button_texts


def test_end_to_end_single_run_workspace_flow(monkeypatch):
    """Slice 26 — één analyse, geen scenario-split."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    app.processEvents()

    kpi_model = window.kpi_table_view.model()
    assert kpi_model.columnCount() == 2
    assert kpi_model.data(kpi_model.index(0, 1), Qt.DisplayRole) != "—"

    for mode in (MODE_LCC, MODE_BIJDRAGEN, MODE_FM_DETAIL):
        window.workspace_state.set_modus(mode)
        app.processEvents()

    window._state.set_last_project(None)
    app.processEvents()
    window._state.set_last_project(_three_level_project())
    app.processEvents()

    fresh_model = window.kpi_table_view.model()
    for r in range(fresh_model.rowCount()):
        assert fresh_model.data(fresh_model.index(r, 1), Qt.DisplayRole) == "—"


def test_workspace_toolbar_no_longer_contains_legacy_run_or_compare_buttons(
    monkeypatch,
):
    """Slice 26 — één analyse-knop, geen CM/PM of legacy compare."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert getattr(window, "run_button", None) is None
    assert getattr(window, "compare_button", None) is None
    assert getattr(window, "run_cm_button", None) is None
    assert getattr(window, "run_pm_button", None) is None
    assert window.run_analyse_button is not None
    assert window.run_analyse_button.text() == messages.WORKSPACE_START_ANALYSE_BUTTON_LABEL


def test_workspace_window_clears_run_state_on_new_project_path(monkeypatch):
    """Loading another project clears tree-totals back to structure-only `—` cells."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    window._state.set_last_project(_three_level_project())
    window._state.set_last_run(_done_run_for_fixture())
    app.processEvents()
    model = window.pbs_tree_view.model()
    first_root_index_with_totals = model.index(0, 2)
    assert model.data(first_root_index_with_totals, Qt.DisplayRole) != "—"

    # Changing path clears run/project state; the tree empties until a new project is loaded.
    window.path_input.setText("another-path.rcm.json")
    app.processEvents()
    assert window._state.last_run is None
    assert window._state.last_project is None

    # Reloading another project re-attaches the structure-only tree (numeric cells `—`).
    window._state.set_last_project(_three_level_project())
    app.processEvents()
    model_after = window.pbs_tree_view.model()
    assert model_after is not None
    assert model_after.rowCount() >= 1
    first_root_after = model_after.index(0, 2)
    assert model_after.data(first_root_after, Qt.DisplayRole) == "—"


def test_workspace_window_default_modus_is_bijdragen_with_niet_beschikbaarheid_pbs(
    monkeypatch,
):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    snapshot = window.workspace_state.snapshot()
    assert snapshot.modus == MODE_BIJDRAGEN
    assert snapshot.metric == METRIC_NIET_BESCHIKBAARHEID
    assert snapshot.source == SOURCE_PBS


def test_modus_segmented_control_exposes_three_buttons_with_bijdragen_checked(
    monkeypatch,
):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert set(window.modus_buttons.keys()) == {
        "bijdragen",
        "lcc",
        "fm_detail",
    }
    assert window.modus_buttons["bijdragen"].isChecked() is True
    for key, btn in window.modus_buttons.items():
        if key != "bijdragen":
            assert btn.isChecked() is False


def test_clicking_modus_button_switches_workspace_state_modus(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    window.modus_buttons["fm_detail"].click()
    app.processEvents()

    assert window.workspace_state.snapshot().modus == MODE_FM_DETAIL


def test_switching_modus_changes_visible_detail_page(monkeypatch):
    """Modus-switch leads the detail zone to swap to the matching page."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    # Bijdragen page is initial.
    assert window.detail_stack.currentWidget() is window.bijdragen_page

    window.modus_buttons["fm_detail"].click()
    app.processEvents()
    assert window.detail_stack.currentWidget() is window.fm_detail_page

    window.modus_buttons["lcc"].click()
    app.processEvents()
    assert window.detail_stack.currentWidget() is window.lcc_page

    window.modus_buttons["bijdragen"].click()
    app.processEvents()
    assert window.detail_stack.currentWidget() is window.bijdragen_page


def test_bijdragen_modus_renders_top_n_contribution_rows_after_run(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    run = _done_run_for_fixture()
    window._state.set_last_run(run)
    app.processEvents()

    chart_rows = window.bijdragen_chart_widget.rows()
    assert len(chart_rows) >= 1
    table_model = window.bijdragen_table_view.model()
    assert table_model is not None
    assert table_model.rowCount() == len(chart_rows)


def test_changing_metric_combo_updates_contribution_rows(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    run = _done_run_for_fixture()
    window._state.set_last_run(run)
    app.processEvents()

    initial = window.bijdragen_chart_widget.rows()
    initial_values = tuple(r.value for r in initial)

    # Switch to METRIC_KOSTEN; values should change (kosten vs unavailability are different units/magnitudes).
    idx = window.metric_combo.findData(METRIC_KOSTEN)
    window.metric_combo.setCurrentIndex(idx)
    app.processEvents()

    new_values = tuple(r.value for r in window.bijdragen_chart_widget.rows())
    assert new_values != initial_values
    assert window.workspace_state.snapshot().metric == METRIC_KOSTEN


def test_clicking_faalwijze_source_toggle_switches_to_fm_grouping(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    run = _done_run_for_fixture()
    window._state.set_last_run(run)
    app.processEvents()

    window.source_toggle_faalwijze_button.click()
    app.processEvents()

    assert window.workspace_state.snapshot().source == SOURCE_FAALWIJZE
    rows = window.bijdragen_chart_widget.rows()
    # In faalwijze-mode the category_id is fm_id, not pbs_id.
    assert all(r.category_id.startswith("FM-") for r in rows)


def test_pbs_scope_filters_both_bijdragen_chart_and_fm_table(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    run = _done_run_for_fixture()
    window._state.set_last_run(run)
    app.processEvents()

    pbs_ids = list(project.pbs_items)
    window.set_pbs_scope(pbs_ids[-1])
    app.processEvents()

    # Bijdragen-chart only contains rows under scope (only one PBS).
    chart_rows = window.bijdragen_chart_widget.rows()
    assert all(r.category_id == pbs_ids[-1] for r in chart_rows)

    # FM-detail page should restrict to FM-B.
    window.modus_buttons["fm_detail"].click()
    app.processEvents()
    fm_model = window.fm_table_view.model()
    fm_ids = {
        fm_model.data(fm_model.index(r, 0), Qt.DisplayRole)
        for r in range(fm_model.rowCount())
    }
    assert fm_ids == {"FM-B"}


def test_pbs_scope_survives_modus_switch_to_fm_detail_and_back(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    run = _done_run_for_fixture()
    window._state.set_last_run(run)
    pbs_ids = list(project.pbs_items)
    window.set_pbs_scope(pbs_ids[-1])
    app.processEvents()

    window.modus_buttons["fm_detail"].click()
    app.processEvents()
    window.modus_buttons["bijdragen"].click()
    app.processEvents()

    assert window.workspace_state.snapshot().scope_id == pbs_ids[-1]
    rows = window.bijdragen_chart_widget.rows()
    assert all(r.category_id == pbs_ids[-1] for r in rows)


def test_lcc_modus_without_run_shows_empty_state_label(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    app.processEvents()

    window.modus_buttons["lcc"].click()
    app.processEvents()

    assert window.detail_stack.currentWidget() is window.lcc_page
    assert window.lcc_empty_state_label.isVisible() is True
    assert window.lcc_chart_widget.buckets() == ()
    table_model = window.lcc_table_view.model()
    assert table_model is None or table_model.rowCount() == 0


def test_lcc_modus_after_run_shows_chart_and_table_with_ltap_horizon_buckets(monkeypatch):
    from pathlib import Path as _Path

    from rcm_core.lcc_profile import ltap_horizon_bucket_count
    from rcm_desktop.adapter.run_service import run as run_single

    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    rr = run_single(
        project,
        _Path("tests/fixtures/sample_project.rcm.json"),
        full_recompute=True,
        parallel=False,
    )
    window._state.set_last_run(rr)
    app.processEvents()

    window.modus_buttons["lcc"].click()
    app.processEvents()

    expected_n = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    assert len(window.lcc_chart_widget.buckets()) == expected_n
    table_model = window.lcc_table_view.model()
    assert table_model is not None
    assert table_model.rowCount() == expected_n
    assert window.lcc_empty_state_label.isVisible() is False


def test_lcc_modus_button_tooltip_mentions_project_total_disclaimer(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    tooltip = window.modus_buttons["lcc"].toolTip()
    assert "project-totaal" in tooltip.lower() or "scope" in tooltip.lower()


def test_top10_subbar_visible_only_in_bijdragen_modus(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.top10_subbar.isVisible() is True
    window.modus_buttons["lcc"].click()
    app.processEvents()
    assert window.top10_subbar.isVisible() is False
    window.modus_buttons["bijdragen"].click()
    app.processEvents()
    assert window.top10_subbar.isVisible() is True


def test_legacy_niet_beschikbaarheid_modus_migrates_to_bijdragen(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    window.workspace_state.set_modus("niet_beschikbaarheid")
    app.processEvents()
    assert window.workspace_state.snapshot().modus == MODE_BIJDRAGEN
    assert window.detail_stack.currentWidget() is window.bijdragen_page


def test_lcc_modus_shows_planning_chart_after_run(monkeypatch):
    from pathlib import Path as _Path

    from rcm_desktop.adapter.run_service import run as run_single

    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    rr = run_single(
        project,
        _Path("tests/fixtures/sample_project.rcm.json"),
        full_recompute=True,
        parallel=False,
    )
    window._state.set_last_run(rr)
    app.processEvents()

    window.modus_buttons["lcc"].click()
    app.processEvents()

    assert window.detail_stack.currentWidget() is window.lcc_page
    assert len(window.lcc_chart_widget.buckets()) >= 1


def test_legacy_preventief_modus_migrates_to_lcc(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    window.workspace_state.set_modus("preventief_onderhoud")
    app.processEvents()
    assert window.workspace_state.snapshot().modus == MODE_LCC
    assert window.detail_stack.currentWidget() is window.lcc_page


def test_pm_scope_filter_restricts_chart_and_table(monkeypatch):
    from pathlib import Path as _Path

    from rcm_desktop.adapter.run_service import run as run_single

    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    rr = run_single(
        project,
        _Path("tests/fixtures/sample_project.rcm.json"),
        full_recompute=True,
        parallel=False,
    )
    window._state.set_last_run(rr)
    window.modus_buttons["lcc"].click()
    app.processEvents()

    project_total = sum(
        b.correctief_eur + b.preventief_eur for b in window.lcc_chart_widget.buckets()
    )
    if project_total <= 0:
        return
    pbs_id = next(iter({fr.pbs_id for fr in rr.fm_core_results}))
    window.set_pbs_scope(pbs_id)
    app.processEvents()

    scoped_total = sum(
        b.correctief_eur + b.preventief_eur for b in window.lcc_chart_widget.buckets()
    )
    assert scoped_total <= project_total + 1e-3


def test_switch_bijdragen_lcc_bijdragen_preserves_metric_and_source(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    run = _done_run_for_fixture()
    window._state.set_last_run(run)
    app.processEvents()

    window.metric_combo.setCurrentIndex(window.metric_combo.findData(METRIC_KOSTEN))
    window.source_toggle_faalwijze_button.click()
    app.processEvents()
    assert window.workspace_state.snapshot().metric == METRIC_KOSTEN
    assert window.workspace_state.snapshot().source == SOURCE_FAALWIJZE

    window.modus_buttons["lcc"].click()
    app.processEvents()
    window.modus_buttons["bijdragen"].click()
    app.processEvents()

    snap = window.workspace_state.snapshot()
    assert snap.metric == METRIC_KOSTEN
    assert snap.source == SOURCE_FAALWIJZE


def test_inactive_mode_is_not_computed_until_visible(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    calls = {"lcc": 0, "contrib": 0}

    def _count_lcc(*_a, **_k):
        calls["lcc"] += 1
        return None

    def _count_contrib(*_a, **_k):
        calls["contrib"] += 1
        return ()

    monkeypatch.setattr(
        "rcm_desktop.views.results_workspace_window.build_lcc_planning_curve_reconciled",
        _count_lcc,
    )
    monkeypatch.setattr(
        "rcm_desktop.views.results_workspace_window.build_contribution_rows",
        _count_contrib,
    )

    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    window._project_total_presentation = None
    app.processEvents()
    calls.update({"lcc": 0, "contrib": 0})

    window.workspace_state.set_modus(MODE_LCC)
    app.processEvents()
    assert calls["lcc"] == 1
    assert calls["contrib"] == 0

    window.workspace_state.set_modus(MODE_FM_DETAIL)
    app.processEvents()
    assert calls["lcc"] == 1
    assert calls["contrib"] == 0


def test_validate_result_renders_status_and_summary(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    window._state.set_last_result(
        ValidateResult(
            status="invalid",
            summary="Validatie mislukt met 2 fout(en).",
            details=[
                DetailItem(
                    severity="error",
                    code="FM_NMF_REQUIRES_TEST",
                    message="Niet-evidente faalwijze zonder IN/TST.",
                    context="FM-001",
                ),
            ],
        )
    )
    app.processEvents()

    assert window.validate_status_label.text() == "Ongeldig"
    assert "2 fout" in window.validate_summary_label.text()
    assert "FM_NMF_REQUIRES_TEST" in window.validate_summary_label.toolTip()


def test_run_analyse_button_present_and_disabled_until_validated(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.run_analyse_button is not None
    assert window.run_analyse_button.isEnabled() is False


def test_kpi_table_shows_single_column_with_em_dashes_initially(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    model = window.kpi_table_view.model()
    assert model.columnCount() == 2
    assert model.rowCount() == 4
    for r in range(model.rowCount()):
        assert model.data(model.index(r, 1), Qt.DisplayRole) == "—"


def test_run_fills_huidige_analyse_kpi_column(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    app.processEvents()

    model = window.kpi_table_view.model()
    assert model.headerData(1, Qt.Horizontal, Qt.DisplayRole) == "Huidige analyse"
    assert model.data(model.index(0, 1), Qt.DisplayRole) != "—"


def test_pbs_scope_scales_kpi_rows_1_to_3_but_not_row_4(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    run = _inject_run(window, project)
    app.processEvents()

    model_full = window.kpi_table_view.model()
    full_failures = model_full.data(model_full.index(0, 1), Qt.DisplayRole)
    full_pm_count = model_full.data(model_full.index(3, 1), Qt.DisplayRole)

    pbs_id = next(iter({fr.pbs_id for fr in run.fm_core_results}))
    window.set_pbs_scope(pbs_id)
    app.processEvents()

    model_scoped = window.kpi_table_view.model()
    scoped_failures = model_scoped.data(model_scoped.index(0, 1), Qt.DisplayRole)
    scoped_pm_count = model_scoped.data(model_scoped.index(3, 1), Qt.DisplayRole)
    assert scoped_failures != full_failures or scoped_failures == "0"
    assert scoped_pm_count == full_pm_count


def test_loading_a_different_project_clears_kpi_values(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    app.processEvents()

    window._state.set_last_project(None)
    app.processEvents()
    window._state.set_last_project(_three_level_project())
    app.processEvents()

    model = window.kpi_table_view.model()
    for r in range(model.rowCount()):
        assert model.data(model.index(r, 1), Qt.DisplayRole) == "—"


def test_loading_new_project_resets_modus_and_metric_to_defaults(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    # Drift away from defaults.
    window.workspace_state.set_modus(MODE_FM_DETAIL)
    window.workspace_state.set_metric(METRIC_KOSTEN)
    pbs_ids = list(project.pbs_items)
    window.set_pbs_scope(pbs_ids[-1])
    app.processEvents()

    # Now reload another project (same fixture instance is fine).
    window._state.set_last_project(_three_level_project())
    app.processEvents()

    snapshot = window.workspace_state.snapshot()
    assert snapshot.modus == MODE_BIJDRAGEN
    assert snapshot.metric == METRIC_NIET_BESCHIKBAARHEID
    assert snapshot.scope_id is None


# --------------------------------------------------------------------------
# Slice 26 — single-pane presentatie (geen scenario-split)
# --------------------------------------------------------------------------


def test_run_analyse_enabled_after_validation(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    window._state.set_last_result(
        ValidateResult(status="valid", summary="ok", details=[])
    )
    window._state.set_last_project(_three_level_project())
    app.processEvents()

    assert window.run_analyse_button.isEnabled() is True


def test_lcc_page_never_shows_scenario_split_after_run(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    window.workspace_state.set_modus(MODE_LCC)
    app.processEvents()

    assert window.lcc_single_slot_pane.isVisible() is True


def test_modus_switches_use_single_pane_after_run(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    window.workspace_state.set_modus(MODE_LCC)
    app.processEvents()
    assert window.lcc_single_slot_pane.isVisible() is True

    window.workspace_state.set_modus(MODE_BIJDRAGEN)
    app.processEvents()
    assert window.bijdragen_single_slot_pane.isVisible() is True


def test_pbs_scope_applies_to_bijdragen_single_pane(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    run = _inject_run(window, project)
    window.workspace_state.set_modus(MODE_BIJDRAGEN)
    app.processEvents()

    pbs_id = next(iter({fr.pbs_id for fr in run.fm_core_results}))
    window.set_pbs_scope(pbs_id)
    app.processEvents()
    scoped_rows = window.bijdragen_table_view.model().rowCount()

    window.show_whole_project_button.click()
    app.processEvents()
    full_rows = window.bijdragen_table_view.model().rowCount()
    assert full_rows >= scoped_rows


def test_lcc_modus_reuses_render_index_without_second_build(monkeypatch):
    """Slice 37 — LCC bouwt via render_index; tweede bezoek hergebruikt cache."""
    import rcm_desktop.adapter.lcc_planning_service as lcc_planning
    import rcm_desktop.adapter.presentation_lazy_service as lazy_svc

    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    run = _inject_run(window, project)
    app.processEvents()

    calls = {"n": 0}
    real = lcc_planning.build_lcc_planning_curve_reconciled

    def counting(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(lazy_svc, "build_lcc_planning_curve_reconciled", counting)
    window.workspace_state.set_modus(MODE_LCC)
    app.processEvents()
    window.workspace_state.set_modus(MODE_BIJDRAGEN)
    app.processEvents()
    window.workspace_state.set_modus(MODE_LCC)
    app.processEvents()
    assert calls["n"] == 1


def test_validate_hydrates_run_from_cache_without_runner(monkeypatch, tmp_path):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    project_path = tmp_path / "demo.rcm.json"
    project_path.write_text(
        Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    from rcm_desktop.adapter.presentation_cache_service import (
        attach_presentation_to_cache,
        build_project_total_presentation,
    )

    run = run_single(project, project_path)
    attach_presentation_to_cache(
        project_path, project, build_project_total_presentation(project, run)
    )
    window.path_input.setText(str(project_path))
    window._state.set_last_project(project)
    window._after_project_validated(project)
    app.processEvents()

    assert window._state.last_run is not None
    assert window._state.last_run.status == "done"
    assert window.run_analyse_button.text() == messages.WORKSPACE_RECOMPUTE_ANALYSE_BUTTON_LABEL


def test_fm_detail_selection_shows_inspector_identity_and_lifecycle(monkeypatch):
    """Slice 34 issue 03 — FM-inspector na rijselectie."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    window._state.set_last_run(_done_run_for_fixture())
    window.modus_buttons["fm_detail"].click()
    app.processEvents()

    model = window.fm_table_view.model()
    assert model is not None and model.rowCount() >= 1
    window.fm_table_view.selectRow(0)
    app.processEvents()

    assert window.fm_inspector_panel.isVisible()
    assert "FM-A" in window.fm_inspector_identity_label.text()
    lifecycle_text = window.fm_inspector_lifecycle_label.text()
    assert messages.WORKSPACE_FM_INSPECTOR_FAALMOMENTEN in lifecycle_text
    assert window.fm_inspector_hash_label.text()
    assert messages.WORKSPACE_FM_INSPECTOR_HASH_PREFIX in window.fm_inspector_hash_label.text()


def test_fm_inspector_selection_after_scope_rerender(monkeypatch):
    """Inspector blijft reageren op rijselectie na FM-tabel re-render (proxy wiring)."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    window._state.set_last_run(_done_run_for_fixture())
    window.modus_buttons["fm_detail"].click()
    app.processEvents()

    window.fm_table_view.selectRow(0)
    app.processEvents()
    assert window.fm_inspector_panel.isVisible()
    assert "FM-A" in window.fm_inspector_identity_label.text()

    window.show_whole_project_button.click()
    app.processEvents()

    model = window.fm_table_view.model()
    fm_b_row = next(
        row
        for row in range(model.rowCount())
        if model.data(model.index(row, 0), Qt.DisplayRole) == "FM-B"
    )
    window.fm_table_view.selectRow(fm_b_row)
    app.processEvents()

    assert window.fm_inspector_panel.isVisible()
    assert "FM-B" in window.fm_inspector_identity_label.text()


def test_fm_table_sorts_by_total_cost_column(monkeypatch):
    """FM-tabel sorteert numeriek via proxy + RAW_ROLE (kolom totale kosten)."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    window._state.set_last_run(_done_run_for_fixture())
    window.modus_buttons["fm_detail"].click()
    app.processEvents()

    model = window.fm_table_view.model()
    assert model is not None and model.rowCount() == 2
    window.fm_table_view.sortByColumn(6, Qt.DescendingOrder)
    app.processEvents()

    top_fm = model.data(model.index(0, 0), Qt.DisplayRole)
    bottom_fm = model.data(model.index(1, 0), Qt.DisplayRole)
    assert top_fm == "FM-B"
    assert bottom_fm == "FM-A"


def test_fm_detail_inspector_empty_without_selection(monkeypatch):
    """Slice 34 issue 03 — lege staat zonder FM-selectie."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    window._state.set_last_run(_done_run_for_fixture())
    window.modus_buttons["fm_detail"].click()
    app.processEvents()

    assert window.fm_inspector_empty_label.isVisible()
    assert not window.fm_inspector_panel.isVisible()


def _done_run_fm_a_with_horizon_profile() -> RunResult:
    project = _three_level_project()
    pbs_ids = list(project.pbs_items)
    num = 5
    hp = FMHorizonProfile(
        cor_eur=[20.0] * num,
        cor_downtime_hr=[2.0, 2.0, 2.0, 2.0, 2.0],
        hidden_nb_hr=[0.5, 0.0, 0.0, 0.0, 0.0],
    )
    fm_core = (
        FMResult(
            fm_id="FM-A",
            pbs_id=pbs_ids[0],
            p_failure_lifecycle=0.4,
            expected_failures=0.0,
            expected_raw_downtime_hr=9.5,
            expected_detection_delay_hr=0.5,
            expected_total_downtime_hr=10.0,
            expected_pm_downtime_hr=0.0,
            expected_cm_cost_eur=100.0,
            pm_cost_eur=80.0,
            total_cost_eur=200.0,
            risk_contribution=0.2,
            horizon_profile=hp,
        ),
        FMResult(
            fm_id="FM-B",
            pbs_id=pbs_ids[-1],
            p_failure_lifecycle=0.6,
            expected_failures=6.0,
            expected_raw_downtime_hr=9.5,
            expected_detection_delay_hr=0.5,
            expected_total_downtime_hr=10.0,
            expected_pm_downtime_hr=0.0,
            expected_cm_cost_eur=180.0,
            pm_cost_eur=120.0,
            total_cost_eur=300.0,
            risk_contribution=0.3,
        ),
    )
    base = _done_run_for_fixture()
    return RunResult(
        status=base.status,
        summary=base.summary,
        metrics=base.metrics,
        fm_core_results=fm_core,
        rows=base.rows,
        pbs_rows=base.pbs_rows,
    )


def test_fm_detail_inspector_shows_year_table_and_reconcile(monkeypatch):
    """Slice 34 issue 04 — jaartabel + reconcile in inspector."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    window._state.set_last_run(_done_run_fm_a_with_horizon_profile())
    window.modus_buttons["fm_detail"].click()
    app.processEvents()

    window.fm_table_view.selectRow(0)
    app.processEvents()

    year_model = window.fm_inspector_year_table_view.model()
    assert year_model is not None
    assert year_model.rowCount() >= 1
    assert year_model.data(year_model.index(0, 0), Qt.DisplayRole) == "2026"
    reconcile_text = window.fm_inspector_reconcile_label.text()
    assert messages.WORKSPACE_FM_INSPECTOR_RECONCILE_OK in reconcile_text
    assert not window.fm_inspector_profile_missing_label.isVisible()


def test_fm_detail_inspector_profile_missing_without_horizon(monkeypatch):
    """Slice 34 issue 04 — melding bij ontbrekend horizon_profile."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    window._state.set_last_run(_done_run_for_fixture())
    window.modus_buttons["fm_detail"].click()
    app.processEvents()
    window.fm_table_view.selectRow(0)
    app.processEvents()

    assert window.fm_inspector_profile_missing_label.isVisible()
    assert messages.WORKSPACE_FM_INSPECTOR_PROFILE_MISSING in (
        window.fm_inspector_profile_missing_label.text()
    )
    assert messages.WORKSPACE_FM_INSPECTOR_RECONCILE_WARN in (
        window.fm_inspector_reconcile_label.text()
    )


def test_fm_detail_inspector_hidden_in_top10_modus(monkeypatch):
    """Slice 34 issue 03 — inspector alleen in FM-detail."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    window._state.set_last_run(_done_run_for_fixture())
    window.modus_buttons["bijdragen"].click()
    app.processEvents()

    assert not window.fm_inspector_container.isVisible()


def _done_run_sample_fm001() -> RunResult:
    """RunResult met FM-001 zodat FM-detail-tabel en project overeenkomen."""
    project = _three_level_project()
    fm_core = (
        FMResult(
            fm_id="FM-001",
            pbs_id="PBS-001-1",
            p_failure_lifecycle=0.4,
            expected_failures=4.0,
            expected_raw_downtime_hr=9.5,
            expected_detection_delay_hr=0.5,
            expected_total_downtime_hr=10.0,
            expected_pm_downtime_hr=0.0,
            expected_cm_cost_eur=120.0,
            pm_cost_eur=80.0,
            total_cost_eur=200.0,
            risk_contribution=0.2,
        ),
    )
    from rcm_desktop.adapter.run_service import build_run_result

    return build_run_result(project, list(fm_core), summary_prefix="test")


def test_fm_double_click_opens_editor_only_in_fm_detail(monkeypatch):
    """Slice 44 — dubbelklik opent editor alleen in FM-detail."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    opened: list[str] = []

    class _FakeDialog:
        DialogCode = QDialog.DialogCode

        def __init__(self, _parent, **kwargs) -> None:
            self.commit_result = None
            self._fm_id = kwargs.get("fm_id", "")

        def exec(self):
            opened.append(self._fm_id)
            return QDialog.DialogCode.Rejected

    monkeypatch.setattr(
        "rcm_desktop.views.results_workspace_window.FmEditorDialog",
        _FakeDialog,
    )
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    window._state.set_last_run(_done_run_sample_fm001())
    window.modus_buttons["bijdragen"].click()
    app.processEvents()
    model = window.fm_table_view.model()
    idx = model.index(0, 0)
    window.fm_table_view.doubleClicked.emit(idx)
    app.processEvents()
    assert opened == []

    window.modus_buttons["fm_detail"].click()
    app.processEvents()
    model = window.fm_table_view.model()
    assert model is not None and model.rowCount() >= 1
    window.fm_table_view.selectRow(0)
    app.processEvents()
    sel = window.fm_table_view.selectedIndexes()
    assert sel
    window.fm_table_view.doubleClicked.emit(sel[0])
    app.processEvents()
    assert opened == ["FM-001"]


def test_fm_editor_ok_updates_mttf_and_triggers_incremental_run(monkeypatch, tmp_path):
    """Slice 44 smoke — OK in editor wijzigt MTTF en roept incrementele run aan."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    from rcm_core.incremental_run import IncrementalRunResult
    from rcm_desktop.adapter.fm_edit_commit_service import FmEditCommitResult
    from rcm_desktop.adapter.run_service import RunMetrics, build_run_result
    from rcm_core.models import FMResult

    project = _three_level_project()
    path = tmp_path / "proj.rcm.json"
    path.write_text(
        Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8")
    )

    class _AcceptDialog:
        DialogCode = QDialog.DialogCode

        def __init__(self, _parent, **kwargs) -> None:
            self._project = kwargs["project"]
            self._fm_id = kwargs["fm_id"]
            self.commit_result = None

        def exec(self):
            from rcm_desktop.adapter.fm_edit_bundle_service import load_bundle
            from rcm_desktop.adapter.fm_edit_commit_service import (
                apply_bundle_scope,
                commit_edits,
                create_edit_session,
            )

            fm_id = self._fm_id
            if fm_id not in self._project.faalwijzes:
                fm_id = "FM-001"
            session = create_edit_session(self._project)
            bundle = load_bundle(self._project, fm_id)
            row = dict(bundle.faalwijze_row)
            row["mttf_jaar"] = 99.0
            bundle = type(bundle)(
                fm_id=bundle.fm_id,
                faalwijze_row=row,
                pbs_row=bundle.pbs_row,
                fm_effect_rows=bundle.fm_effect_rows,
                pm_task_rows=bundle.pm_task_rows,
                pm_effect_rows=bundle.pm_effect_rows,
                task_group_rows=bundle.task_group_rows,
                effect_klasse_rows=bundle.effect_klasse_rows,
            )
            apply_bundle_scope(session, bundle)

            mock_fm = FMResult(
                fm_id=fm_id,
                pbs_id=row["pbs_id"],
                p_failure_lifecycle=0.1,
                expected_failures=1.0,
                expected_raw_downtime_hr=0.0,
                expected_detection_delay_hr=0.0,
                expected_total_downtime_hr=0.0,
                expected_pm_downtime_hr=0.0,
                expected_cm_cost_eur=0.0,
                pm_cost_eur=0.0,
                total_cost_eur=0.0,
                risk_contribution=0.0,
            )
            monkeypatch.setattr(
                "rcm_desktop.adapter.fm_edit_commit_service.run_incremental_analysis",
                lambda *_a, **_k: IncrementalRunResult(
                    fm_results={fm_id: mock_fm},
                    pbs_results={},
                    cache_only=False,
                    affected_fm_ids=[fm_id],
                    recalculated_fm_count=1,
                ),
            )
            built = session.build_project()
            run = build_run_result(built, [mock_fm], summary_prefix="test")
            self.commit_result = FmEditCommitResult(
                ok=True,
                errors=(),
                affected_fm_ids=(fm_id,),
                project=built,
                run_result=run,
            )
            return QDialog.DialogCode.Accepted

    monkeypatch.setattr(
        "rcm_desktop.views.results_workspace_window.FmEditorDialog",
        _AcceptDialog,
    )
    window = ResultsWorkspaceWindow()
    window.show()
    window.path_input.setText(str(path))
    window._state.set_last_project(project, path=str(path))
    window._state.set_last_run(_done_run_sample_fm001())
    window.modus_buttons["fm_detail"].click()
    app.processEvents()
    window.fm_table_view.selectRow(0)
    app.processEvents()
    sel = window.fm_table_view.selectedIndexes()
    window.fm_table_view.doubleClicked.emit(sel[0])
    app.processEvents()

    assert window._state.last_project is not None
    assert window._state.last_project.faalwijzes["FM-001"].mttf_jaar == pytest.approx(99.0)
