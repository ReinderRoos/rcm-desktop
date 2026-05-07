"""Tests voor CLI-runbeleid in rcm_core.cli.

Tests voor `cmd_serve` (Streamlit) zijn verwijderd: dat subcommando is in RCM2
niet meegeporteerd; zie scrub-list in RCM2_REFERENTIE.md.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core import cli as rcm


def _args(**overrides):
    base = {"no_parallel": False, "parallel": False}
    base.update(overrides)
    return argparse.Namespace(**base)


def test_resolve_parallel_default_windows_is_sequential(monkeypatch):
    monkeypatch.setattr(rcm.sys, "platform", "win32")
    assert rcm._resolve_parallel_execution(_args()) is False


def test_resolve_parallel_default_non_windows_is_parallel(monkeypatch):
    monkeypatch.setattr(rcm.sys, "platform", "linux")
    assert rcm._resolve_parallel_execution(_args()) is True


def test_resolve_parallel_explicit_parallel_opt_in(monkeypatch):
    monkeypatch.setattr(rcm.sys, "platform", "win32")
    assert rcm._resolve_parallel_execution(_args(parallel=True)) is True


def test_resolve_parallel_no_parallel_has_priority(monkeypatch):
    monkeypatch.setattr(rcm.sys, "platform", "linux")
    assert rcm._resolve_parallel_execution(_args(parallel=True, no_parallel=True)) is False
