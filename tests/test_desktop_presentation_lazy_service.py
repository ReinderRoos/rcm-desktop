from __future__ import annotations

from rcm_desktop.adapter.presentation_lazy_service import (
    lcc_presentation_uses_render_index,
    presentation_rebuild_needed_for_lcc,
    startup_presentation_modi,
)
from rcm_desktop.adapter.results_workspace_state import MODE_BIJDRAGEN


def test_startup_presentation_modi_is_bijdragen_only():
    assert startup_presentation_modi() == frozenset({MODE_BIJDRAGEN})


def test_lcc_uses_render_index_not_presentation_cache():
    assert lcc_presentation_uses_render_index() is True


def test_presentation_rebuild_not_needed_for_lcc_without_cache(tmp_path):
    from rcm_core.persistence import load_project

    fixture = __import__("pathlib").Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    project_path = tmp_path / "demo.rcm.json"
    project_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    assert presentation_rebuild_needed_for_lcc(project, str(project_path)) is False
