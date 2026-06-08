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
    assert messages.WORKSPACE_MODE_LCC == "Tijdsplot"
    assert messages.WORKSPACE_SOURCE_TOGGLE_PBS == "Component"


def test_workspace_window_shows_renamed_modus_buttons(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.modus_buttons[MODE_BIJDRAGEN].text() == "Top 10"
    assert window.modus_buttons[MODE_LCC].text() == "Tijdsplot"
    assert window.source_toggle_pbs_button.text() == "Component"


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


# --- Prio 1: KPI collapse + geen dubbele placeholder ---


def test_kpi_collapse_hides_table_in_lcc_modus(monkeypatch):
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

    assert window.kpi_collapse_button.isVisible() is True
    assert window.workspace_state.snapshot().kpi_collapsed_in_lcc is True
    assert window.kpi_table_view.isVisible() is False
    assert window.kpi_collapse_button.text() == "▶"

    window.kpi_collapse_button.click()
    app.processEvents()

    assert window.workspace_state.snapshot().kpi_collapsed_in_lcc is False
    assert window.kpi_table_view.isVisible() is True
    assert window.kpi_collapse_button.text() == "▼"

    window.kpi_collapse_button.click()
    app.processEvents()

    assert window.kpi_table_view.isVisible() is False
    assert window.kpi_collapse_button.text() == "▶"


def test_kpi_placeholder_not_visible_after_layout(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.kpi_placeholder.isVisible() is False
