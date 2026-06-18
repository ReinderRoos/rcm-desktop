"""Slice 32 UX prio's 1–3: KPI-inklap, faalwijze+component, labels Top 10/Tijdsplot/Component."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox, QApplication

from rcm_core.config import RCMConfig
from rcm_core.models import FMResult, Faalwijze, PBSItem, RCMProject
from rcm_desktop import messages
from rcm_desktop.adapter.contribution_chart_service import build_contribution_rows
from rcm_desktop.adapter.result_view_service import build_pbs_rows, build_rows
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_KOSTEN,
    MODE_BIJDRAGEN,
    MODE_LCC,
    SOURCE_FAALWIJZE,
)
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import (
    _done_run_for_fixture,
    _ensure_app,
    _inject_run,
    _three_level_project,
)


def _project_duplicate_faalwijze_omschrijving() -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=80.0),
        pbs_items={
            "ROOT": PBSItem("ROOT", "obj", "el", "Root"),
            "PBS-A": PBSItem("PBS-A", "obj", "el", "Pomp A", parent_pbs_id="ROOT"),
            "PBS-B": PBSItem("PBS-B", "obj", "el", "Pomp B", parent_pbs_id="ROOT"),
        },
        faalwijzes={
            "FM-1": Faalwijze(
                fm_id="FM-1",
                pbs_id="PBS-A",
                functie_id="FUNC",
                faalwijze_omschrijving="Sensor drift buiten kalibratie",
            ),
            "FM-2": Faalwijze(
                fm_id="FM-2",
                pbs_id="PBS-B",
                functie_id="FUNC",
                faalwijze_omschrijving="Sensor drift buiten kalibratie",
            ),
        },
    )


def _run_for(project: RCMProject, fm_results: list[FMResult]) -> RunResult:
    rows = build_rows(project, fm_results)
    pbs_rows = build_pbs_rows(project, {})
    metrics = RunMetrics(
        fm_result_count=len(fm_results),
        total_lifecycle_faalmomenten=sum(r.expected_failures for r in fm_results),
        total_cost_eur=sum(r.total_cost_eur for r in fm_results),
        total_downtime_hr=sum(
            r.expected_total_downtime_hr + r.expected_pm_downtime_hr for r in fm_results
        ),
        lifecycle_years=float(project.config.lifecycle_years),
        total_risk_contribution=sum(r.risk_contribution for r in fm_results),
    )
    return RunResult(
        status="done",
        summary="ok",
        metrics=metrics,
        rows=rows,
        pbs_rows=pbs_rows,
        fm_core_results=tuple(fm_results),
    )


# --- Prio 3: labels (adapter/constants) ---


def test_workspace_mode_labels_renamed():
    assert messages.WORKSPACE_MODE_BIJDRAGEN == "Top 10"
    assert messages.WORKSPACE_MODE_LCC == "LCC-plot"
    assert messages.WORKSPACE_SOURCE_TOGGLE_PBS == "Component"


def test_workspace_window_shows_view_tab_labels(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    nav = window._workspace_navigation
    labels = [btn.text() for btn in nav.view_tab_buttons.values()]
    assert labels == ["KPI", "LCC", "LTAP", "TopX"]
    assert not hasattr(window, "source_toggle_pbs_button")


# --- Prio 2: faalwijze label + component ---


def test_faalwijze_labels_include_component_name():
    project = _project_duplicate_faalwijze_omschrijving()
    fm_results = [
        FMResult(
            fm_id="FM-1",
            pbs_id="PBS-A",
            p_failure_lifecycle=0.1,
            expected_failures=1.0,
            expected_raw_downtime_hr=1.0,
            expected_detection_delay_hr=0.0,
            expected_total_downtime_hr=1.0,
            expected_pm_downtime_hr=0.0,
            expected_cm_cost_eur=500.0,
            pm_cost_eur=0.0,
            total_cost_eur=500.0,
            risk_contribution=0.1,
            effect_bijdragen={},
        ),
        FMResult(
            fm_id="FM-2",
            pbs_id="PBS-B",
            p_failure_lifecycle=0.1,
            expected_failures=1.0,
            expected_raw_downtime_hr=1.0,
            expected_detection_delay_hr=0.0,
            expected_total_downtime_hr=1.0,
            expected_pm_downtime_hr=0.0,
            expected_cm_cost_eur=250.0,
            pm_cost_eur=0.0,
            total_cost_eur=250.0,
            risk_contribution=0.05,
            effect_bijdragen={},
        ),
    ]
    run = _run_for(project, fm_results)

    rows = build_contribution_rows(
        project,
        run,
        source=SOURCE_FAALWIJZE,
        metric=METRIC_KOSTEN,
        top_n=10,
        scope_id=None,
    )

    labels = {r.label for r in rows}
    assert "Pomp A — Sensor drift buiten kalibratie" in labels
    assert "Pomp B — Sensor drift buiten kalibratie" in labels


# --- Prio 1: KPI als view + geen dubbele placeholder ---


def test_kpi_view_navigates_from_menu(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    app.processEvents()

    window.workspace_state.set_modus(MODE_LCC)
    app.processEvents()

    kpi_action = window._workspace_menu.actions_by_id["view.output.kpi_overview"]
    assert kpi_action.isVisible() is True
    kpi_action.trigger()
    app.processEvents()

    assert window.workspace_state.snapshot().active_view_id == "output.kpi_overview"
    assert window.detail_stack.currentWidget() is window.kpi_overview_page
    assert window.kpi_table_view.isVisible() is True


def test_kpi_placeholder_not_visible_after_layout(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.kpi_placeholder.isVisible() is False
