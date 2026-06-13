from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_core.persistence import load_project
from rcm_desktop.adapter.entity_edit_service import EntityEditService
from rcm_desktop.views.validate_faalwijzen_panel import ValidateFaalwijzenPanel


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def test_panel_mount_filter_and_bulk(sample_project):
    _ensure_app()
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(sample_project)
    panel = ValidateFaalwijzenPanel()
    panel.attach(svc, sample_project)
    panel._filter_failure.setCurrentIndex(1)
    panel._on_filter_changed()
    visible = panel._proxy.visible_fm_ids()
    assert visible
    result = svc.apply_bulk_change(visible[:1], "failure_type", "aging")
    assert result.ok is True
    panel.refresh_view()
