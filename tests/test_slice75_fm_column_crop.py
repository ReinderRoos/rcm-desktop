"""Slice 75 issue 02 — Bijsnijden-knop (regelomloop) + QSettings op FM-detail-tabel."""



from __future__ import annotations



import pytest



pytest.importorskip("PySide6")



from PySide6.QtCore import QSettings

from PySide6.QtWidgets import QHeaderView, QMessageBox



from rcm_desktop.adapter.column_fit_policy import ColumnFitMode, default_column_fit_mode

from rcm_desktop.adapter.column_fit_settings import (

    FM_DETAIL_COLUMN_FIT_SETTINGS_KEY,

    column_fit_mode_from_crop_checked,

    crop_checked_from_column_fit_mode,

    read_fm_detail_column_fit_mode,

    write_fm_detail_column_fit_mode,

)

from rcm_desktop.adapter.column_fit_policy import FM_DETAIL_COL_FAALWIJZE

from rcm_desktop.views.panels.fm_detail_workspace_panel import build_fm_detail_workspace_panel

from rcm_desktop.views.panels.workspace_table_policy import (

    ElideTooltipTableDelegate,

    WordWrapTableDelegate,

)



from tests.test_desktop_results_workspace_window import _ensure_app

from tests.test_slice74_window import _window_in_fm_detail





@pytest.fixture(autouse=True)

def _isolated_column_fit_settings(tmp_path):

    """Voorkom dat lokale of eerdere test-settings de kolom-fit-tests beïnvloeden."""

    from PySide6.QtCore import QSettings



    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))

    QSettings("rcm2", "desktop").clear()

    yield





class _FakeSettings:

    def __init__(self) -> None:

        self._data: dict[str, object] = {}



    def value(self, key: str, default: object = None, type: type | None = None) -> object:

        return self._data.get(key, default)



    def setValue(self, key: str, value: object) -> None:

        self._data[key] = value





def test_fm_detail_panel_exposes_bijsnijden_toggle() -> None:

    _ensure_app()

    panel = build_fm_detail_workspace_panel()

    assert panel.column_crop_button is not None

    assert panel.column_crop_button.isCheckable()





def test_settings_default_is_passend() -> None:

    settings = _FakeSettings()

    assert read_fm_detail_column_fit_mode(settings) is ColumnFitMode.PASSEND





def test_settings_round_trip_bijgesneden() -> None:

    settings = _FakeSettings()

    write_fm_detail_column_fit_mode(settings, ColumnFitMode.BIJGESNEDEN)

    assert settings._data[FM_DETAIL_COLUMN_FIT_SETTINGS_KEY] == "bijgesneden"

    assert read_fm_detail_column_fit_mode(settings) is ColumnFitMode.BIJGESNEDEN





def test_crop_checked_maps_to_modes() -> None:

    assert column_fit_mode_from_crop_checked(False) is ColumnFitMode.PASSEND

    assert column_fit_mode_from_crop_checked(True) is ColumnFitMode.BIJGESNEDEN

    assert crop_checked_from_column_fit_mode(default_column_fit_mode()) is False





def test_column_crop_toggle_switches_word_wrap(monkeypatch) -> None:

    app, window = _window_in_fm_detail(monkeypatch)

    header = window.fm_table_view.horizontalHeader()

    assert header.sectionResizeMode(FM_DETAIL_COL_FAALWIJZE) == QHeaderView.ResizeMode.Stretch

    assert window.fm_table_view.wordWrap() is True

    assert isinstance(window.fm_table_view.itemDelegate(), WordWrapTableDelegate)



    window._workspace_menu.actions_by_id["view.column_crop"].setChecked(True)

    app.processEvents()

    assert window.fm_table_view.wordWrap() is False

    assert isinstance(window.fm_table_view.itemDelegate(), ElideTooltipTableDelegate)





def test_column_crop_mode_persists_across_window_rebuild(monkeypatch) -> None:

    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow



    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)



    app = _ensure_app()

    window = ResultsWorkspaceWindow()

    window._workspace_menu.actions_by_id["view.column_crop"].setChecked(True)

    app.processEvents()

    rebuilt = ResultsWorkspaceWindow()

    app.processEvents()

    assert rebuilt._workspace_menu.actions_by_id["view.column_crop"].isChecked() is True

    assert rebuilt._fm_column_fit_mode is ColumnFitMode.BIJGESNEDEN

    assert rebuilt.fm_table_view.wordWrap() is False


