from __future__ import annotations

import json
from pathlib import Path

from rcm_core.models import RCMProject

from rcm_desktop.adapter.project_path_resolution_service import resolve_project_file_path


def _sample_project() -> RCMProject:
    raw = json.loads(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def test_resolve_prefers_session_path() -> None:
    session = Path("C:/projects/a.rcm")
    text = "C:/other/b.rcm"
    resolved = resolve_project_file_path(session_path=session, path_text=text)
    assert resolved.file_path == session


def test_resolve_falls_back_to_path_text() -> None:
    resolved = resolve_project_file_path(
        session_path=None,
        path_text="  tests/fixtures/sample_project.rcm.json  ",
    )
    assert resolved.file_path == Path("tests/fixtures/sample_project.rcm.json")


def test_resolve_empty_when_both_missing() -> None:
    resolved = resolve_project_file_path(session_path=None, path_text="   ")
    assert resolved.file_path is None


def test_cache_path_follows_project_file() -> None:
    project_path = Path("tests/fixtures/sample_project.rcm.json")
    resolved = resolve_project_file_path(session_path=project_path, path_text="")
    assert resolved.cache_path() == project_path.with_suffix("").with_suffix(
        ".rcm.cache.json"
    )


def test_default_report_output_path() -> None:
    project_path = Path("tests/fixtures/sample_project.rcm.json")
    resolved = resolve_project_file_path(session_path=project_path, path_text="")
    out = resolved.default_report_output_path(_sample_project())
    assert out is not None
    assert out.parent.name == "rapporten"
    assert out.suffix == ".docx"
