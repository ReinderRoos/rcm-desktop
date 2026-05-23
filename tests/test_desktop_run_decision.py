"""Slice 36 issue 01 — run-beslissingsmodule (Qt-vrij)."""
from __future__ import annotations

from rcm_desktop.adapter.run_decision import RunUserIntent, resolve_run_execution


def test_force_recompute_uses_full_recompute_sequential():
    opts = resolve_run_execution(user_intent=RunUserIntent.FORCE_RECOMPUTE)
    assert opts.full_recompute is True
    assert opts.parallel is False


def test_start_analyse_uses_incremental_path_sequential():
    opts = resolve_run_execution(user_intent=RunUserIntent.START_ANALYSE)
    assert opts.full_recompute is False
    assert opts.parallel is False
