"""Slice 85 — effectfilter pruning, toolbar-plaatsing, LCC-aslabels."""

from __future__ import annotations

from PySide6.QtCore import Qt

from rcm_core.config import RCMConfig
from rcm_core.effect_impact_service import (
    EffectNbFilterSet,
    HIDDEN_NB_RESTPOST_ID,
    list_nb_effect_klassen,
)
from rcm_core.effect_taxonomy import CATEGORIE_BESCHIKBAARHEID
from rcm_core.models import (
    EffectKlasse,
    FMEffectLink,
    FMResult,
    Faalwijze,
    PBSItem,
    RCMProject,
)
from rcm_core.units import TimeDuration, TimeUnit
from rcm_desktop import messages
from rcm_desktop.adapter.lcc_plot_axis_labels import lcc_plot_axis_labels
from rcm_desktop.adapter.nb_effect_filter_presentation import (
    build_nb_effect_filter_presentation,
)
from rcm_desktop.adapter.results_workspace_orchestrator import (
    FmToolbarPlan,
    ResultsWorkspaceOrchestrator,
)
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    MODE_LCC,
    ResultsWorkspaceState,
    WorkspaceStateSnapshot,
)
from rcm_desktop.views.widgets.nb_effect_filter_combo import NbEffectFilterCombo


def _snap(**kwargs) -> WorkspaceStateSnapshot:
    base = ResultsWorkspaceState().snapshot()
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    data.update(kwargs)
    return WorkspaceStateSnapshot(**data)


def _project_two_pbs() -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=5.0, modeljaar=2020),
        pbs_items={
            "PBS-A": PBSItem("PBS-A", "o", "e", "A"),
            "PBS-B": PBSItem("PBS-B", "o", "e", "B"),
        },
        faalwijzes={
            "FM-A": Faalwijze(
                fm_id="FM-A",
                pbs_id="PBS-A",
                functie_id="F",
                faalwijze_omschrijving="A",
                mttf_jaar=10.0,
                downtime_per_failure=TimeDuration(10.0, TimeUnit.HOURS),
            ),
            "FM-B": Faalwijze(
                fm_id="FM-B",
                pbs_id="PBS-B",
                functie_id="F",
                faalwijze_omschrijving="B",
                mttf_jaar=10.0,
                downtime_per_failure=TimeDuration(5.0, TimeUnit.HOURS),
            ),
        },
        effect_klassen={
            "AV-1": EffectKlasse("AV-1", "Actief", "F", CATEGORIE_BESCHIKBAARHEID),
            "AV-EMPTY": EffectKlasse("AV-EMPTY", "Leeg", "F", CATEGORIE_BESCHIKBAARHEID),
        },
        fm_effect_links={
            "L1": FMEffectLink("L1", "FM-A", "AV-1", 1.0),
            "L2": FMEffectLink("L2", "FM-A", "AV-EMPTY", 1.0),
            "L3": FMEffectLink("L3", "FM-B", "AV-EMPTY", 1.0),
        },
    )


def _fmr_active() -> FMResult:
    return FMResult(
        fm_id="FM-A",
        pbs_id="PBS-A",
        p_failure_lifecycle=0.5,
        expected_failures=1.0,
        expected_raw_downtime_hr=8.0,
        expected_detection_delay_hr=2.0,
        expected_total_downtime_hr=10.0,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=0.0,
        pm_cost_eur=0.0,
        total_cost_eur=0.0,
        risk_contribution=0.0,
        fm_effect_bijdragen={"AV-1": 1.0, "AV-EMPTY": 0.0},
        fm_effect_bijdragen_per_jaar={"AV-1": [0.2] * 5},
    )


def _fmr_empty_only() -> FMResult:
    return FMResult(
        fm_id="FM-B",
        pbs_id="PBS-B",
        p_failure_lifecycle=0.0,
        expected_failures=0.0,
        expected_raw_downtime_hr=0.0,
        expected_detection_delay_hr=0.0,
        expected_total_downtime_hr=0.0,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=0.0,
        pm_cost_eur=0.0,
        total_cost_eur=0.0,
        risk_contribution=0.0,
        fm_effect_bijdragen={"AV-EMPTY": 0.0},
    )


def test_zero_contribution_class_is_not_selectable() -> None:
    project = _project_two_pbs()
    fm_results = (_fmr_active(), _fmr_empty_only())
    plan = build_nb_effect_filter_presentation(project, fm_results)
    by_id = {e.klasse_id: e for e in plan.entries}
    assert by_id["AV-1"].selectable is True
    assert by_id["AV-1"].disabled_reason is None
    assert by_id["AV-EMPTY"].selectable is False
    assert by_id["AV-EMPTY"].disabled_reason == messages.WORKSPACE_NB_EFFECT_FILTER_DISABLED_REASON


def test_contribution_ignores_pbs_scope_selection() -> None:
    project = _project_two_pbs()
    fm_results = (_fmr_active(),)
    scoped = build_nb_effect_filter_presentation(
        project, fm_results, scope_id="PBS-B"
    )
    by_id = {e.klasse_id: e for e in scoped.entries}
    assert by_id["AV-1"].selectable is True


def test_selected_class_stays_checked_when_becomes_disabled(qtbot) -> None:
    project = _project_two_pbs()
    fm_results = (_fmr_active(), _fmr_empty_only())
    plan = build_nb_effect_filter_presentation(project, fm_results)
    combo = NbEffectFilterCombo()
    qtbot.addWidget(combo)
    combo.set_presentation(plan)
    combo.set_filter(EffectNbFilterSet(selected_klasse_ids=frozenset({"AV-EMPTY"})))
    model = combo.model()
    for row in range(model.rowCount()):
        item = model.item(row)
        if item is None:
            continue
        if str(item.data(Qt.UserRole)) == "AV-EMPTY":
            assert item.checkState() == Qt.CheckState.Checked
            assert not (item.flags() & Qt.ItemFlag.ItemIsEnabled)
            assert item.toolTip() == messages.WORKSPACE_NB_EFFECT_FILTER_DISABLED_REASON


def test_disabled_item_is_not_toggleable(qtbot) -> None:
    project = _project_two_pbs()
    plan = build_nb_effect_filter_presentation(project, (_fmr_active(), _fmr_empty_only()))
    combo = NbEffectFilterCombo()
    qtbot.addWidget(combo)
    combo.set_presentation(plan)
    combo.set_filter(EffectNbFilterSet())
    model = combo.model()
    empty_row = next(
        row
        for row in range(model.rowCount())
        if str(model.item(row).data(Qt.UserRole)) == "AV-EMPTY"
    )
    item = model.item(empty_row)
    assert not (item.flags() & Qt.ItemFlag.ItemIsEnabled)
    assert item.toolTip() == messages.WORKSPACE_NB_EFFECT_FILTER_DISABLED_REASON
    combo.view().pressed.emit(model.index(empty_row, 0))
    assert combo.current_filter().is_all()


def test_toolbar_plans_place_effect_filter_in_shared_row() -> None:
    for modus in (MODE_BIJDRAGEN, MODE_LCC, MODE_FM_DETAIL):
        snap = _snap(modus=modus, metric=METRIC_NIET_BESCHIKBAARHEID)
        plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
        assert plan.shared_toolbar.effect_nb_filter_in_shared_row is True


def test_fm_toolbar_no_longer_has_evident_filter() -> None:
    assert "fm_evident_filter_visible" not in FmToolbarPlan.__dataclass_fields__


def test_lcc_axis_labels_per_metric() -> None:
    x, y = lcc_plot_axis_labels(METRIC_FAALMOMENTEN)
    assert x == messages.LCC_PLOT_AXIS_X_KALENDERJAREN
    assert y == messages.LCC_PLOT_AXIS_Y_FAALMOMENTEN
    _, y_nb_h = lcc_plot_axis_labels(
        METRIC_NIET_BESCHIKBAARHEID, unavailability_display="hours"
    )
    _, y_nb_p = lcc_plot_axis_labels(
        METRIC_NIET_BESCHIKBAARHEID, unavailability_display="percent"
    )
    assert y_nb_h == messages.LCC_PLOT_AXIS_Y_NB_HOURS
    assert y_nb_p == messages.LCC_PLOT_AXIS_Y_NB_PERCENT
    _, y_k = lcc_plot_axis_labels(METRIC_KOSTEN)
    assert y_k == messages.LCC_PLOT_AXIS_Y_KOSTEN


def test_lcc_axis_labels_golden_strings() -> None:
    assert messages.LCC_PLOT_AXIS_X_KALENDERJAREN == "Kalenderjaren"
    assert "falen" in messages.LCC_PLOT_AXIS_Y_FAALMOMENTEN.lower()
    assert "€" in messages.LCC_PLOT_AXIS_Y_KOSTEN


def test_list_nb_effect_klassen_still_includes_all_classes() -> None:
    project = _project_two_pbs()
    ids = {kid for kid, _ in list_nb_effect_klassen(project)}
    assert "AV-1" in ids
    assert "AV-EMPTY" in ids
    assert HIDDEN_NB_RESTPOST_ID in ids
