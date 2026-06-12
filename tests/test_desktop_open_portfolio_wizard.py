"""Slice 64 — pytest-qt smoke: portfolio wizard → save → validate."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pytestqt")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_desktop.adapter.portfolio_wizard_service import (
    complete_portfolio_merge,
    preview_portfolio_scan,
)
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow


def _write_minimal_rcm(path: Path, *, fm_id: str = "FM-001") -> None:
    path.write_text(
        f'{{"config":{{"lifecycle_years":40,"modeljaar":2026}},'
        f'"pbs_items":{{"PBS-001":{{"pbs_id":"PBS-001","object_naam":"O","element_naam":"E","bouwdeel_naam":"B"}}}},'
        f'"faalwijzes":{{"{fm_id}":{{"fm_id":"{fm_id}","pbs_id":"PBS-001","functie_id":"F1","faalwijze_omschrijving":"X","failure_type":"random","mttf_jaar":10}}}}}}',
        encoding="utf-8",
    )


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_open_portfolio_wizard_smoke(monkeypatch, qtbot, tmp_path: Path) -> None:
    _ensure_app()
    scan_root = tmp_path / "sync"
    schakel = scan_root / "Houtrib"
    schakel.mkdir(parents=True)
    _write_minimal_rcm(schakel / "a.rcm.json")

    preview = preview_portfolio_scan(scan_root)
    wizard_result = complete_portfolio_merge(
        preview,
        selected_relative_paths=[preview.rows[0].relative_path],
        portfolio_name="Smoke portfolio",
    )
    save_path = tmp_path / "merged.rcm.json"

    monkeypatch.setattr(
        "rcm_desktop.views.results_workspace_window.run_portfolio_wizard_with_root_picker",
        lambda *args, **kwargs: wizard_result,
    )
    monkeypatch.setattr(
        "rcm_desktop.views.results_workspace_window.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(save_path), ""),
    )

    window = ResultsWorkspaceWindow()
    qtbot.addWidget(window)
    window._open_portfolio_wizard()

    assert save_path.is_file()
    assert window.path_input.text() == str(save_path)
    assert window._state.last_project is not None
    assert window._state.last_project.projectnaam == "Smoke portfolio"
    assert window._state.last_preview is not None
