"""Tests voor portfolio_scan (ADR-0009, grill 5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.portfolio_scan import (
    MAX_FILE_BYTES,
    scan_portfolio_root,
)


def _write_minimal_rcm(path: Path) -> None:
    path.write_text(
        '{"config":{"lifecycle_years":40,"modeljaar":2026},"faalwijzes":{}}',
        encoding="utf-8",
    )


def test_scan_finds_rcm_json_under_netwerkschakel(tmp_path: Path) -> None:
    houtrib = tmp_path / "Houtrib"
    houtrib.mkdir()
    _write_minimal_rcm(houtrib / "demo.rcm.json")

    result = scan_portfolio_root(tmp_path)
    assert len(result.hits) == 1
    assert result.hits[0].netwerkschakel_label == "Houtrib"
    assert result.hits[0].source_type == "rcm_json"
    assert result.hits[0].relative_path == "Houtrib/demo.rcm.json"
    assert len(result.hits[0].sha256) == 64


def test_scan_uses_netwerkschakel_yaml_label(tmp_path: Path) -> None:
    folder = tmp_path / "NS-01"
    folder.mkdir()
    (folder / "netwerkschakel.yaml").write_text('label: "Roggebot"\n', encoding="utf-8")
    _write_minimal_rcm(folder / "model.rcm.json")

    result = scan_portfolio_root(tmp_path)
    assert result.hits[0].netwerkschakel_label == "Roggebot"


def test_scan_skips_symlink(tmp_path: Path) -> None:
    schakel = tmp_path / "Houtrib"
    schakel.mkdir()
    target = schakel / "real.rcm.json"
    _write_minimal_rcm(target)
    link = schakel / "linked.rcm.json"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlinks not supported on this platform")

    result = scan_portfolio_root(tmp_path)
    assert len(result.hits) == 1
    assert any("Symlink" in err for err in result.errors)


def test_scan_rejects_oversized_file(tmp_path: Path) -> None:
    schakel = tmp_path / "Big"
    schakel.mkdir()
    big = schakel / "big.rcm.json"
    big.write_bytes(b"x" * (MAX_FILE_BYTES + 1))

    result = scan_portfolio_root(tmp_path)
    assert result.hits == []
    assert any("te groot" in err for err in result.errors)


def test_scan_to_manifest_relative_paths_only(tmp_path: Path) -> None:
    schakel = tmp_path / "Ramspol"
    schakel.mkdir()
    _write_minimal_rcm(schakel / "x.rcm.json")

    manifest = scan_portfolio_root(tmp_path, store_absolute_paths=False).to_manifest(
        scan_root_label="MNN"
    )
    assert manifest.scan_root_label == "MNN"
    assert manifest.store_absolute_paths is False
    assert manifest.sources[0].relative_path == "Ramspol/x.rcm.json"


def test_scan_finds_rcm_cost_xlsx(tmp_path: Path) -> None:
    schakel = tmp_path / "Gaarkeuken"
    schakel.mkdir()
    xlsx = schakel / "RCMCostdata export_Gaarkeuken.xlsx"
    xlsx.write_bytes(b"PK\x03\x04fake")

    result = scan_portfolio_root(tmp_path)
    assert len(result.hits) == 1
    assert result.hits[0].source_type == "xlsx"
