"""Slice 105 issues 05–06 — what-if topmenu + geen scenario CM/PM."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from rcm_desktop import messages
from rcm_desktop.adapter.results_workspace_state import MODE_FM_DETAIL, MODE_LCC
from rcm_desktop.adapter.workspace_menu_spec import WORKSPACE_MENU_SPEC
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app
from tests.workspace_test_helpers import switch_workspace_modus


def test_whatif_is_top_level_menu_section() -> None:
    menu_ids = [section.menu_id for section in WORKSPACE_MENU_SPEC]
    assert menu_ids.index("whatif") < menu_ids.index("run")
    whatif = next(section for section in WORKSPACE_MENU_SPEC if section.menu_id == "whatif")
    assert whatif.label == messages.WORKSPACE_MENU_WHATIF
    assert whatif.items[0].action_id == "whatif.toggle"


def test_scenario_cm_pm_menu_items_removed() -> None:
    action_ids = {item.action_id for section in WORKSPACE_MENU_SPEC for item in section.items}
    assert "run.scenario_cm" not in action_ids
    assert "run.scenario_pm" not in action_ids
    assert "run.toggle_whatif" not in action_ids


def test_whatif_menu_from_fm_navigates_to_lcc(monkeypatch) -> None:
    app = _ensure_app()
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    switch_workspace_modus(window, "fm_detail", app)
    assert window.workspace_state.snapshot().modus == MODE_FM_DETAIL
    window._toggle_lcc_whatif_from_menu()
    app.processEvents()
    snap = window.workspace_state.snapshot()
    assert snap.modus == MODE_LCC
    assert snap.planning_overlay.active is True
