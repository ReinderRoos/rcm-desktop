"""Adapter tests for workspace_session_service (slice 53 PR1b)."""

from __future__ import annotations

from rcm_core.models import FailureType, Faalwijze, Functie, PBSItem, RCMProject
from rcm_core.config import RCMConfig

from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter import workspace_session_service as wss


def _session() -> ProjectSession:
    cfg = RCMConfig(lifecycle_years=40.0, modeljaar=2026)
    pbs = PBSItem("PBS-1", "Obj", "El", "BD", bouwjaar=2000)
    func = Functie("F-1", "PBS-1", "Functie")
    fm = Faalwijze(
        "FM-1",
        "PBS-1",
        "F-1",
        "Test",
        failure_type=FailureType.RANDOM,
        mttf_jaar=10.0,
    )
    project = RCMProject(
        config=cfg,
        pbs_items={"PBS-1": pbs},
        functies={"F-1": func},
        faalwijzes={"FM-1": fm},
    )
    loaded = LoadedProject.from_core(project)
    return ProjectSession.from_parts(loaded)


def test_fm_exists_and_scope_label() -> None:
    session = _session()
    assert wss.fm_exists(session, "FM-1")
    assert not wss.fm_exists(session, "FM-missing")
    assert wss.scope_bouwdeel_naam(session, "PBS-1") == "BD"
    assert session.loaded.modeljaar == 2026


def test_navigation_and_pbs_structure_builders() -> None:
    session = _session()
    nav_model = wss.build_navigation_tree_model_for_session(session)
    assert nav_model.rowCount() == 1
    roots = wss.build_pbs_structure_tree_for_session(session)
    assert len(roots) == 1
