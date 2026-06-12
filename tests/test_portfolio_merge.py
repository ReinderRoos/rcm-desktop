"""Tests voor portfolio_merge (slice 64 issue 01, ADR-0009)."""

from __future__ import annotations

from pathlib import Path

from rcm_core.config import RCMConfig
from rcm_core.models import Faalwijze, FailureType, PBSItem, RCMProject
from rcm_core.persistence import load_project, save_project
from rcm_core.portfolio_merge import (
    PORTFOLIO_TOP_PBS_ID,
    PortfolioMergeResult,
    PortfolioSource,
    load_portfolio_manifest_sidecar,
    merge_portfolio_sources,
    portfolio_manifest_sidecar_path,
    prefix_entity_id,
    save_portfolio_manifest_sidecar,
)


def _minimal_project(
    *,
    fm_id: str = "FM-001",
    pbs_id: str = "PBS-001",
    lifecycle: float = 40.0,
    modeljaar: int = 2026,
    naam: str = "Demo",
) -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=lifecycle, modeljaar=modeljaar),
        projectnaam=naam,
        pbs_items={
            pbs_id: PBSItem(
                pbs_id=pbs_id,
                object_naam="Obj",
                element_naam="El",
                bouwdeel_naam="Bd",
            )
        },
        faalwijzes={
            fm_id: Faalwijze(
                fm_id=fm_id,
                pbs_id=pbs_id,
                functie_id="FUNC-001",
                faalwijze_omschrijving="Lekkage",
                failure_type=FailureType.RANDOM,
                mttf_jaar=10.0,
            )
        },
    )


def test_prefix_entity_id_uses_netwerkschakel() -> None:
    assert prefix_entity_id("Houtrib", "FM-001") == "Houtrib::FM-001"


def test_merge_two_sources_prefixes_fm_ids_without_collision() -> None:
    a = _minimal_project(fm_id="FM-001", naam="A")
    b = _minimal_project(fm_id="FM-001", naam="B")

    result = merge_portfolio_sources(
        [
            PortfolioSource("src-a", "Houtrib", a, "Houtrib/a.rcm.json"),
            PortfolioSource("src-b", "Roggebot", b, "Roggebot/b.rcm.json"),
        ],
        portfolio_name="MNN Portfolio",
    )

    assert "Houtrib::FM-001" in result.project.faalwijzes
    assert "Roggebot::FM-001" in result.project.faalwijzes
    assert len(result.project.faalwijzes) == 2


def test_merge_places_netwerkschakels_under_fictive_top_pbs() -> None:
    a = _minimal_project()
    b = _minimal_project(fm_id="FM-002")

    result = merge_portfolio_sources(
        [
            PortfolioSource("src-a", "Houtrib", a),
            PortfolioSource("src-b", "Roggebot", b),
        ],
    )

    top = result.project.pbs_items[PORTFOLIO_TOP_PBS_ID]
    assert top.parent_pbs_id is None

    houtrib_root = result.project.pbs_items[prefix_entity_id("Houtrib", "SCHAKEL-ROOT")]
    assert houtrib_root.parent_pbs_id == PORTFOLIO_TOP_PBS_ID

    houtrib_pbs = result.project.pbs_items[prefix_entity_id("Houtrib", "PBS-001")]
    assert houtrib_pbs.parent_pbs_id == prefix_entity_id("Houtrib", "SCHAKEL-ROOT")


def test_merge_manifest_records_id_map_and_source_metadata() -> None:
    a = _minimal_project(lifecycle=40.0, modeljaar=2026)
    b = _minimal_project(lifecycle=50.0, modeljaar=2025, fm_id="FM-002")

    result = merge_portfolio_sources(
        [
            PortfolioSource("src-a", "Houtrib", a, "Houtrib/a.rcm.json"),
            PortfolioSource("src-b", "Roggebot", b, "Roggebot/b.rcm.json"),
        ],
        scan_root_label="MNN",
    )

    assert result.manifest.id_map["src-a::FM-001"] == "Houtrib::FM-001"
    assert result.manifest.id_map["src-b::FM-002"] == "Roggebot::FM-002"
    assert len(result.manifest.sources) == 2
    assert result.manifest.sources[0].lifecycle_years == 40.0
    assert result.manifest.sources[1].modeljaar == 2025
    assert result.manifest.modeljaar_warnings() == ["WARN_MODELJAAR_MISMATCH"]


def test_merge_two_fixture_projects(tmp_path: Path) -> None:
    """2-fixture POC — sample_project + one_fm_planning."""
    fixture_dir = Path("tests/fixtures")
    a = load_project(fixture_dir / "one_fm_planning.rcm.json")
    b = load_project(fixture_dir / "sample_project.rcm.json")

    result = merge_portfolio_sources(
        [
            PortfolioSource("planning", "Planning", a, "Planning/one.rcm.json"),
            PortfolioSource("sample", "Sample", b, "Sample/sample.rcm.json"),
        ],
        portfolio_name="Fixture portfolio",
    )

    assert len(result.project.faalwijzes) == len(a.faalwijzes) + len(b.faalwijzes)
    assert PORTFOLIO_TOP_PBS_ID in result.project.pbs_items
    assert result.project.projectnaam == "Fixture portfolio"


def test_manifest_sidecar_round_trip(tmp_path: Path) -> None:
    project_path = tmp_path / "portfolio.rcm.json"
    result = merge_portfolio_sources(
        [PortfolioSource("s1", "Houtrib", _minimal_project())],
    )
    save_project(result.project, project_path)
    save_portfolio_manifest_sidecar(result.manifest, project_path)

    sidecar = portfolio_manifest_sidecar_path(project_path)
    assert sidecar.is_file()

    loaded = load_portfolio_manifest_sidecar(project_path)
    assert loaded is not None
    assert loaded.id_map == result.manifest.id_map
