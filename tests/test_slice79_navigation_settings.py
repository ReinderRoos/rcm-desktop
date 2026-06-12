"""Slice 79 issue 03 — navigatie persistentie via QSettings."""

from __future__ import annotations

from PySide6.QtCore import QSettings

from rcm_desktop.adapter.workspace_navigation_settings import (
    read_workspace_navigation,
    write_workspace_navigation,
)
from rcm_desktop.adapter.workspace_view_registry import SIDE_OUTPUT


def test_read_unknown_view_id_falls_back_to_side_default() -> None:
    class FakeSettings:
        def __init__(self) -> None:
            self._data: dict[str, object] = {
                "workspace/navigation/side": SIDE_OUTPUT,
                "workspace/navigation/sticky/output": "output.unknown",
            }

        def value(self, key: str, default: object = ...) -> object:
            return self._data.get(key, default)

        def setValue(self, key: str, value: object) -> None:
            self._data[key] = value

    side, sticky = read_workspace_navigation(FakeSettings())
    assert side == SIDE_OUTPUT
    assert sticky["output"] == "output.top_10"


def test_write_and_read_round_trip() -> None:
    class FakeSettings:
        def __init__(self) -> None:
            self._data: dict[str, object] = {}

        def value(self, key: str, default: object = ...) -> object:
            return self._data.get(key, default)

        def setValue(self, key: str, value: object) -> None:
            self._data[key] = value

    settings = FakeSettings()
    write_workspace_navigation(
        settings,
        workspace_side=SIDE_OUTPUT,
        sticky_by_side={"output": "output.lcc_plot", "input": "input.faalwijzen"},
    )
    side, sticky = read_workspace_navigation(settings)
    assert side == SIDE_OUTPUT
    assert sticky["output"] == "output.lcc_plot"
