"""Issue 07 — Qt navigation tree model (pytest-qt)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QApplication, QTreeView

from rcm_desktop.adapter.isograph_import_service import build_from_sheets
from rcm_desktop.adapter.rcm_navigation_tree_builder import build_rcm_navigation_tree
from rcm_desktop.adapter.rcm_navigation_tree_model import RcmNavigationTreeModel


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _import_project():
    return build_from_sheets(
        {
            "RcmLocations": [{"Id": "L2", "Parent": "", "Description": "Sub"}],
            "RcmFunctions": [{"Id": "F1", "Parent": "L2", "Description": "Functie"}],
            "RcmFunctionalFailures": [{"Id": "FF1", "Parent": "F1", "Description": "FF"}],
            "RcmCauses": [
                {
                    "Id": "FM-A",
                    "Parent": "FF1",
                    "Description": "A",
                    "LocationId": "L2",
                    "FmMttf": 87600,
                    "FmStd": 0,
                    "InitialAge": 8760,
                    "Mttr": 8,
                    "FmDistribution": "Normal",
                },
            ],
            "RcmEffects": [{"Id": "E1", "Description": "Effect"}],
            "RcmCauseEffectAssignments": [
                {"Cause": "FM-A", "Effect": "E1", "CEnable": "True", "RedundancyFactor": 1},
            ],
            "RcmCorrectiveTasks": [
                {"Cause": "FM-A", "TaskDuration": 8, "OperationalCost": 1000},
            ],
            "RcmScheduledTasks": [],
            "TaskGroups": [],
            "Project": [{"LifeTime": 876000}],
        },
        modeljaar=2026,
    ).project


def test_navigation_model_lists_fm_under_functie() -> None:
    _ensure_app()
    project = _import_project()
    roots = build_rcm_navigation_tree(project)
    model = RcmNavigationTreeModel(roots, project)
    view = QTreeView()
    view.setModel(model)
    labels: list[str] = []

    def walk(parent: QModelIndex) -> None:
        for r in range(model.rowCount(parent)):
            idx = model.index(r, 0, parent)
            val = model.data(idx, Qt.DisplayRole)
            if val:
                labels.append(str(val))
            if model.rowCount(idx):
                walk(idx)

    walk(QModelIndex())
    assert "FM-A" in labels
    assert "F1" in labels
    assert model.data(model.index(0, 2), Qt.DisplayRole) == "—"
