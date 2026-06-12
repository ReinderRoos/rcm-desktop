"""Slice 80 issue 03 — PBS-Id default verborgen + kolomkeuze."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop import messages
from rcm_desktop.adapter.fm_results_column_policy import FM_COL_PBS_ID
from rcm_desktop.adapter.fm_results_column_settings import (
    read_fm_hidden_optional_columns,
    write_fm_hidden_optional_columns,
)
from rcm_desktop.adapter.fm_results_table_model import FMResultsTableModel
from rcm_desktop.adapter.result_view_service import FMResultRow
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_slice74_window import _window_in_fm_detail


class _FakeSettings:
    def __init__(self) -> None:
        self._data: dict[str, object] = {}

    def value(self, key: str, default: object = None, type: type | None = None) -> object:
        return self._data.get(key, default)

    def setValue(self, key: str, value: object) -> None:
        self._data[key] = value


def test_pbs_id_column_index_and_default_hidden() -> None:
    model = FMResultsTableModel([])
    assert model.columnCount() == 9
    assert model.headerData(FM_COL_PBS_ID, Qt.Horizontal, Qt.DisplayRole) == messages.FM_RESULTS_HEADER_PBS_ID


def test_settings_default_hides_pbs_id() -> None:
    settings = _FakeSettings()
    assert read_fm_hidden_optional_columns(settings) == frozenset({"pbs_id"})


def test_settings_round_trip_show_pbs_id() -> None:
    settings = _FakeSettings()
    write_fm_hidden_optional_columns(settings, frozenset())
    assert read_fm_hidden_optional_columns(settings) == frozenset()


@pytest.fixture(autouse=True)
def _isolated_settings(tmp_path):
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    QSettings("rcm2", "desktop").clear()
    yield


def test_fm_table_hides_pbs_id_by_default(monkeypatch) -> None:
    app, window = _window_in_fm_detail(monkeypatch)
    header = window.fm_table_view.horizontalHeader()
    assert header.isSectionHidden(FM_COL_PBS_ID) is True


def test_fm_table_pbs_id_toggle_via_context_menu(monkeypatch) -> None:
    app, window = _window_in_fm_detail(monkeypatch)
    window._on_fm_optional_column_toggled("pbs_id", True)
    app.processEvents()
    header = window.fm_table_view.horizontalHeader()
    assert header.isSectionHidden(FM_COL_PBS_ID) is False


def test_fm_pbs_id_visibility_persists_across_window_rebuild(monkeypatch) -> None:
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    app = QApplication.instance() or QApplication([])
    window = ResultsWorkspaceWindow()
    window._on_fm_optional_column_toggled("pbs_id", True)
    app.processEvents()
    rebuilt = ResultsWorkspaceWindow()
    app.processEvents()
    header = rebuilt.fm_table_view.horizontalHeader()
    assert header.isSectionHidden(FM_COL_PBS_ID) is False
