"""Tests voor CLI-runbeleid en serve-foutpropagatie."""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))

_RCM_PATH = Path(__file__).parent.parent / "rcm.py"
_SPEC = importlib.util.spec_from_file_location("rcm_cli_module", _RCM_PATH)
assert _SPEC and _SPEC.loader
rcm = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(rcm)


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


def test_cmd_serve_returns_subprocess_returncode(monkeypatch):
    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr("subprocess.run", fake_run)
    result = rcm.cmd_serve(argparse.Namespace(project="awzi_haarlem_waarderpolder_demo.rcm.json"))
    assert result == 7


def test_cmd_serve_missing_streamlit_binary(monkeypatch):
    def fake_run(*_args, **_kwargs):
        raise FileNotFoundError("missing")

    monkeypatch.setattr("subprocess.run", fake_run)
    result = rcm.cmd_serve(argparse.Namespace(project="awzi_haarlem_waarderpolder_demo.rcm.json"))
    assert result == 1
