"""Tests voor portfolio_manifest (ADR-0009)."""

from __future__ import annotations

from rcm_core.portfolio_manifest import (
    WARN_LIFECYCLE_MISMATCH,
    WARN_MODELJAAR_MISMATCH,
    PortfolioManifest,
    PortfolioSourceEntry,
)


def test_lifecycle_warning_when_sources_differ() -> None:
    manifest = PortfolioManifest(
        sources=[
            PortfolioSourceEntry(
                source_id="a",
                netwerkschakel_label="A",
                relative_path="A/model.rcm.json",
                source_type="rcm_json",
                sha256="aa",
                mtime_ns=1,
                lifecycle_years=50.0,
            ),
            PortfolioSourceEntry(
                source_id="b",
                netwerkschakel_label="B",
                relative_path="B/model.rcm.json",
                source_type="rcm_json",
                sha256="bb",
                mtime_ns=2,
                lifecycle_years=80.0,
            ),
        ]
    )
    assert WARN_LIFECYCLE_MISMATCH in manifest.lifecycle_warnings()


def test_modeljaar_warning_when_sources_differ() -> None:
    manifest = PortfolioManifest(
        sources=[
            PortfolioSourceEntry(
                source_id="a",
                netwerkschakel_label="A",
                relative_path="A/model.rcm.json",
                source_type="rcm_json",
                sha256="aa",
                mtime_ns=1,
                modeljaar=2024,
            ),
            PortfolioSourceEntry(
                source_id="b",
                netwerkschakel_label="B",
                relative_path="B/model.rcm.json",
                source_type="rcm_json",
                sha256="bb",
                mtime_ns=2,
                modeljaar=2026,
            ),
        ]
    )
    assert WARN_MODELJAAR_MISMATCH in manifest.modeljaar_warnings()


def test_manifest_round_trip() -> None:
    manifest = PortfolioManifest(
        scan_root_label="MNN-BAP",
        sources=[
            PortfolioSourceEntry(
                source_id="houtrib",
                netwerkschakel_label="Houtrib",
                relative_path="Houtrib/demo.rcm.json",
                source_type="rcm_json",
                sha256="deadbeef",
                mtime_ns=99,
                lifecycle_years=60.0,
                modeljaar=2026,
                fm_count=12,
            )
        ],
        id_map={"FM-1": "Houtrib::FM-1"},
    )
    restored = PortfolioManifest.from_dict(manifest.to_dict())
    assert restored.scan_root_label == "MNN-BAP"
    assert len(restored.sources) == 1
    assert restored.sources[0].fm_count == 12
    assert restored.id_map["FM-1"] == "Houtrib::FM-1"
