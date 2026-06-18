"""Slice 105 issues 17–20 — chrome follow-ups na HILT105 GO."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app


def test_compare_scenario_combo_hidden(monkeypatch) -> None:
    _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    assert window.compare_scenario_combo.isVisible() is False


def test_qss_combobox_max_height_24px() -> None:
    from pathlib import Path

    qss = (Path(__file__).resolve().parents[1] / "rcm_desktop" / "theme" / "rcm2.qss").read_text(
        encoding="utf-8"
    )
    assert "max-height: 24px" in qss
    assert "min-height: 1.2em" in qss


def test_fm_editor_section_nav_qss_present() -> None:
    from pathlib import Path

    qss = (Path(__file__).resolve().parents[1] / "rcm_desktop" / "theme" / "rcm2.qss").read_text(
        encoding="utf-8"
    )
    assert "QListWidget#FmEditorSectionNav" in qss
    assert "::item:selected" in qss
