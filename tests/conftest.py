"""Gedeelde pytest-fixtures voor rcm-desktop."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings


@pytest.fixture
def isolated_navigation_settings(tmp_path):
    """Lege QSettings zodat venstertests niet afhangen van lokale persistentie."""
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    QSettings("rcm2", "desktop").clear()
    yield
    QSettings("rcm2", "desktop").clear()
