"""Tests voor portfolio_wizard_service (slice 64 issue 03)."""

from __future__ import annotations

from pathlib import Path

from rcm_core.persistence import load_project
from rcm_core.portfolio_scan import scan_portfolio_root
from rcm_desktop.adapter.portfolio_wizard_service import (
    complete_portfolio_merge,
    persist_portfolio_wizard_result,
    preview_portfolio_scan,
)


def _write_minimal_rcm(path: Path, *, fm_id: str = "FM-001") -> None:
    path.write_text(
        f'{{"config":{{"lifecycle_years":40,"modeljaar":2026}},'
        f'"pbs_items":{{"PBS-001":{{"pbs_id":"PBS-001","object_naam":"O","element_naam":"E","bouwdeel_naam":"B"}}}},'
        f'"faalwijzes":{{"{fm_id}":{{"fm_id":"{fm_id}","pbs_id":"PBS-001","functie_id":"F1","faalwijze_omschrijving":"X","failure_type":"random","mttf_jaar":10}}}}}}',
        encoding="utf-8",
    )


def test_preview_scan_lists_netwerkschakels(tmp_path: Path) -> None:
    h = tmp_path / "Houtrib"
    h.mkdir()
    _write_minimal_rcm(h / "a.rcm.json")

    preview = preview_portfolio_scan(tmp_path, scan_root_label="MNN")
    assert len(preview.rows) == 1
    assert preview.rows[0].netwerkschakel_label == "Houtrib"
    assert preview.rows[0].fm_count == 1


def test_preview_warns_on_lifecycle_mismatch(tmp_path: Path) -> None:
    a_dir = tmp_path / "A"
    b_dir = tmp_path / "B"
    a_dir.mkdir()
    b_dir.mkdir()
    _write_minimal_rcm(a_dir / "a.rcm.json")
    (b_dir / "b.rcm.json").write_text(
        '{"config":{"lifecycle_years":80,"modeljaar":2026},"faalwijzes":{}}',
        encoding="utf-8",
    )

    preview = preview_portfolio_scan(tmp_path)
    assert "WARN_LIFECYCLE_MISMATCH" in preview.config_warnings


def test_complete_merge_builds_portfolio_from_selected_rows(tmp_path: Path) -> None:
    a_dir = tmp_path / "Houtrib"
    b_dir = tmp_path / "Roggebot"
    a_dir.mkdir()
    b_dir.mkdir()
    _write_minimal_rcm(a_dir / "a.rcm.json", fm_id="FM-A")
    _write_minimal_rcm(b_dir / "b.rcm.json", fm_id="FM-B")

    preview = preview_portfolio_scan(tmp_path)
    result = complete_portfolio_merge(
        preview,
        selected_relative_paths=[r.relative_path for r in preview.rows],
        portfolio_name="Test portfolio",
    )
    assert result.project.projectnaam == "Test portfolio"
    assert len(result.project.faalwijzes) == 2


def test_persist_writes_rcm_and_sidecar(tmp_path: Path) -> None:
    a_dir = tmp_path / "Houtrib"
    a_dir.mkdir()
    _write_minimal_rcm(a_dir / "a.rcm.json")

    preview = preview_portfolio_scan(tmp_path)
    result = complete_portfolio_merge(
        preview,
        selected_relative_paths=[preview.rows[0].relative_path],
        portfolio_name="P",
    )
    out = tmp_path / "out.rcm.json"
    persist_portfolio_wizard_result(result, out)

    assert out.is_file()
    loaded = load_project(out)
    assert loaded.projectnaam == "P"
    sidecar = out.parent / "out.portfolio_manifest.json"
    assert sidecar.is_file()
