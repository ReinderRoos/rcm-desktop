"""Slice 106 issue 01 — active_view_id canonieke navigatie."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_desktop.adapter.results_workspace_orchestrator import ResultsWorkspaceOrchestrator
from rcm_desktop.adapter.results_workspace_state import (
    MODE_FM_DETAIL,
    MODE_LCC,
    ResultsWorkspaceState,
)
from rcm_desktop.adapter.workspace_view_registry import (
    WORKSPACE_VIEW_REGISTRY,
    detail_stack_key_for_view,
    legacy_modus_for_view,
)

RCM_DESKTOP = Path(__file__).resolve().parent.parent / "rcm_desktop"


def test_legacy_modus_derived_from_view_registry() -> None:
    assert legacy_modus_for_view(WORKSPACE_VIEW_REGISTRY, "output.ltap") == MODE_LCC
    assert legacy_modus_for_view(WORKSPACE_VIEW_REGISTRY, "output.lcc_plot") == MODE_LCC
    assert legacy_modus_for_view(WORKSPACE_VIEW_REGISTRY, "output.fm_results") == MODE_FM_DETAIL
    assert legacy_modus_for_view(WORKSPACE_VIEW_REGISTRY, "input.faalwijzen") is None


def test_ltap_and_lcc_plot_share_lcc_detail_stack_key() -> None:
    assert detail_stack_key_for_view(WORKSPACE_VIEW_REGISTRY, "output.ltap") == MODE_LCC
    assert detail_stack_key_for_view(WORKSPACE_VIEW_REGISTRY, "output.lcc_plot") == MODE_LCC


def test_set_modus_lcc_keeps_active_ltap_when_already_on_ltap() -> None:
    state = ResultsWorkspaceState()
    state.set_active_view("output.ltap")
    state.set_modus(MODE_LCC)
    snap = state.snapshot()
    assert snap.active_view_id == "output.ltap"
    assert snap.modus == MODE_LCC


def test_set_modus_lcc_from_fm_uses_first_lcc_view_when_sticky_is_fm() -> None:
    state = ResultsWorkspaceState()
    state.set_active_view("output.ltap")
    state.set_active_view("output.fm_results")
    state.set_modus(MODE_LCC)
    snap = state.snapshot()
    assert snap.active_view_id == "output.lcc_plot"
    assert snap.modus == MODE_LCC


def test_orchestrator_detail_page_key_follows_active_view_id() -> None:
    state = ResultsWorkspaceState()
    state.set_active_view("output.ltap")
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, state.snapshot())
    assert plan.detail_page_modus == MODE_LCC
    assert plan.navigation.active_view_id == "output.ltap"


def test_set_modus_not_used_outside_state_module() -> None:
  offenders: list[str] = []
  for path in RCM_DESKTOP.rglob("*.py"):
      if path.name == "results_workspace_state.py":
          continue
      text = path.read_text(encoding="utf-8")
      if "def set_modus(" in text or ".set_modus(" in text:
          offenders.append(str(path.relative_to(RCM_DESKTOP.parent)))
  assert offenders == [], f"set_modus buiten state: {offenders}"
