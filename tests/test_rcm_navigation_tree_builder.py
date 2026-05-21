"""Issue 07 — navigation tree builder (Qt-free)."""

from rcm_core.config import RCMConfig
from rcm_core.models import Faalwijze, Functie, PBSItem, RCMProject
from rcm_desktop.adapter.rcm_navigation_tree_builder import (
    NavigationNodeKind,
    build_rcm_navigation_tree,
)


def _sample_project() -> RCMProject:
    return RCMProject(
        config=RCMConfig(modeljaar=2026),
        pbs_items={
            "A": PBSItem("A", "o", "e", "Root A"),
            "B": PBSItem("B", "o", "e", "Child B", parent_pbs_id="A"),
        },
        functies={
            "F1": Functie("F1", "A", "Functie op A"),
            "F2": Functie("F2", "B", "Functie op B"),
        },
        faalwijzes={
            "FM-1": Faalwijze(
                fm_id="FM-1",
                functie_id="F1",
                pbs_id="A",
                faalwijze_omschrijving="x",
                eindgevolg="y",
            ),
            "FM-2": Faalwijze(
                fm_id="FM-2",
                functie_id="F1",
                pbs_id="A",
                faalwijze_omschrijving="x2",
                eindgevolg="y2",
            ),
        },
    )


def test_empty_project_yields_no_roots() -> None:
    assert build_rcm_navigation_tree(RCMProject()) == ()


def test_tree_orders_pbs_functie_faalwijze() -> None:
    roots = build_rcm_navigation_tree(_sample_project())
    assert [n.node_id for n in roots] == ["A"]
    root = roots[0]
    assert root.kind == NavigationNodeKind.PBS
    pbs_child = root.children[0]
    assert pbs_child.node_id == "B"
    functie_on_a = root.children[1]
    assert functie_on_a.node_id == "F1"
    assert [c.node_id for c in functie_on_a.children] == ["FM-1", "FM-2"]
    assert functie_on_a.children[0].kind == NavigationNodeKind.FAALWIJZE


def test_imported_project_shows_cause_under_function() -> None:
    from rcm_desktop.adapter.isograph_import_service import build_from_sheets

    sheets = {
        "RcmLocations": [
            {"Id": "L2", "Parent": "", "Description": "Sub"},
        ],
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
    }
    built = build_from_sheets(sheets, modeljaar=2026)
    roots = build_rcm_navigation_tree(built.project)
    assert roots
    functie = roots[0].children[0]
    assert functie.kind == NavigationNodeKind.FUNCTIE
    assert functie.children[0].node_id == "FM-A"
    assert functie.children[0].kind == NavigationNodeKind.FAALWIJZE
