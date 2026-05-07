"""Tests voor editing.pipeline — canoniek project in sessie."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.editing.pipeline import CANONICAL_PROJECT_KEY, promote_built_to_canonical, read_canonical_project
from rcm_core.editing.state import init_edit_state
from rcm_core.models import RCMProject
from rcm_core.persistence import load_project


def _fixture_project():
    fixture = Path(__file__).parent / "fixtures" / "sample_project.rcm.json"
    return load_project(fixture)


def test_read_canonical_roundtrip():
    project = _fixture_project()
    session: dict = {}
    promote_built_to_canonical(session, project)
    assert CANONICAL_PROJECT_KEY in session
    assert session["edit_current"] is not None
    back = read_canonical_project(session)
    assert len(back.faalwijzes) == len(project.faalwijzes)


def test_promote_resets_dirty():
    project = _fixture_project()
    session: dict = {}
    init_edit_state(project, session=session)
    session["edit_dirty_global"] = True
    promote_built_to_canonical(session, project)
    assert session.get("edit_dirty_global") is False
