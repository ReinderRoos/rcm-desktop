"""Tests voor portfolio_wizard_dialog (slice 64 issue 03, pytest-qt)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_desktop.views.portfolio_wizard_dialog import (
    PortfolioWizardDialog,
    PortfolioWizardInput,
    run_portfolio_wizard,
    run_portfolio_wizard_with_root_picker,
)


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _write_minimal_rcm(path: Path) -> None:
    path.write_text(
        '{"config":{"lifecycle_years":40,"modeljaar":2026},'
        '"pbs_items":{"PBS-001":{"pbs_id":"PBS-001","object_naam":"O","element_naam":"E","bouwdeel_naam":"B"}},'
        '"faalwijzes":{"FM-001":{"fm_id":"FM-001","pbs_id":"PBS-001","functie_id":"F1",'
        '"faalwijze_omschrijving":"X","failure_type":"random","mttf_jaar":10}}}',
        encoding="utf-8",
    )


def test_wizard_dialog_accepts_and_returns_merge_result(tmp_path: Path) -> None:
    _ensure_app()
    root = tmp_path / "sync"
    schakel = root / "Houtrib"
    schakel.mkdir(parents=True)
    _write_minimal_rcm(schakel / "model.rcm.json")

    dialog = PortfolioWizardDialog(
        PortfolioWizardInput(scan_root=root, scan_root_label="MNN"),
    )
    dialog._name_edit.setText("Wizard portfolio")
    dialog._on_accept()

    result = dialog.result_value()
    assert result is not None
    assert result.project.projectnaam == "Wizard portfolio"
    assert len(result.project.faalwijzes) == 1


def test_run_portfolio_wizard_none_on_cancel(tmp_path: Path, monkeypatch) -> None:
    _ensure_app()
    root = tmp_path / "sync"
    root.mkdir()

    monkeypatch.setattr(
        "rcm_desktop.views.portfolio_wizard_dialog.PortfolioWizardDialog.exec",
        lambda self: 0,
    )
    assert run_portfolio_wizard(PortfolioWizardInput(scan_root=root)) is None


def test_root_picker_opens_wizard_when_directory_chosen(tmp_path: Path, monkeypatch) -> None:
    _ensure_app()
    root = tmp_path / "sync"
    schakel = root / "Houtrib"
    schakel.mkdir(parents=True)
    _write_minimal_rcm(schakel / "m.rcm.json")

    monkeypatch.setattr(
        "rcm_desktop.views.portfolio_wizard_dialog.QFileDialog.getExistingDirectory",
        lambda *args, **kwargs: str(root),
    )

    def _run(input, parent=None):
        dialog = PortfolioWizardDialog(input, parent=parent)
        dialog._name_edit.setText("Picker portfolio")
        dialog._on_accept()
        return dialog.result_value()

    monkeypatch.setattr(
        "rcm_desktop.views.portfolio_wizard_dialog.run_portfolio_wizard",
        _run,
    )
    result = run_portfolio_wizard_with_root_picker()
    assert result is not None
    assert result.project.projectnaam == "Picker portfolio"
