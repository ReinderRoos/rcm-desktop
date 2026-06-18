"""Tests voor portfolio_run — submodel cache-partitionering (slice 64 issue 02)."""

from __future__ import annotations

from pathlib import Path

from rcm_core.config import RCMConfig
from rcm_core.incremental_run import run_incremental_analysis
from rcm_core.models import Faalwijze, FailureType, PBSItem, RCMProject
from rcm_core.portfolio_merge import PortfolioSource, merge_portfolio_sources
from rcm_core.portfolio_run import (
    extract_submodel_project,
    fm_ids_for_source,
    merge_submodel_fm_results,
    submodel_cache_key,
)


def _minimal_source(
    source_id: str,
    label: str,
    fm_id: str,
    *,
    mttf: float = 10.0,
) -> PortfolioSource:
    project = RCMProject(
        config=RCMConfig(lifecycle_years=40.0, modeljaar=2026),
        pbs_items={
            "PBS-001": PBSItem(
                pbs_id="PBS-001",
                object_naam="O",
                element_naam="E",
                bouwdeel_naam="B",
            )
        },
        faalwijzes={
            fm_id: Faalwijze(
                fm_id=fm_id,
                pbs_id="PBS-001",
                functie_id="FUNC-001",
                faalwijze_omschrijving="Test",
                failure_type=FailureType.RANDOM,
                mttf_jaar=mttf,
            )
        },
    )
    return PortfolioSource(source_id, label, project)


def test_submodel_cache_key_is_stable() -> None:
    assert submodel_cache_key("src-a") == "submodel.src-a"


def test_fm_ids_for_source_returns_prefixed_ids() -> None:
    merged = merge_portfolio_sources(
        [
            _minimal_source("a", "Houtrib", "FM-001"),
            _minimal_source("b", "Roggebot", "FM-002"),
        ],
    )
    ids = fm_ids_for_source(merged.project, merged.manifest, "a")
    assert ids == ["Houtrib::FM-001"]


def test_extract_submodel_project_contains_only_one_schakel(tmp_path: Path) -> None:
    merged = merge_portfolio_sources(
        [
            _minimal_source("a", "Houtrib", "FM-001"),
            _minimal_source("b", "Roggebot", "FM-002"),
        ],
    )
    sub = extract_submodel_project(merged.project, merged.manifest, "a")
    assert sub is not None
    assert len(sub.faalwijzes) == 1
    assert "Roggebot::" not in "".join(sub.faalwijzes.keys())


def test_submodel_run_uses_partitioned_cache(tmp_path: Path) -> None:
    merged = merge_portfolio_sources(
        [
            _minimal_source("a", "Houtrib", "FM-001", mttf=10.0),
            _minimal_source("b", "Roggebot", "FM-002", mttf=12.0),
        ],
    )
    portfolio_path = tmp_path / "portfolio.rcm.json"
    portfolio_path.write_text("{}", encoding="utf-8")

    sub_a = extract_submodel_project(merged.project, merged.manifest, "a")
    assert sub_a is not None
    key_a = submodel_cache_key("a")

    run_incremental_analysis(
        sub_a,
        portfolio_path,
        full_recompute=True,
        parallel=False,
        scenario_key=key_a,
    )

    sub_b = extract_submodel_project(merged.project, merged.manifest, "b")
    assert sub_b is not None
    key_b = submodel_cache_key("b")
    run_incremental_analysis(
        sub_b,
        portfolio_path,
        full_recompute=True,
        parallel=False,
        scenario_key=key_b,
    )

    cache_a = portfolio_path.with_suffix("").with_suffix(f".rcm.cache.{key_a}.json")
    cache_b = portfolio_path.with_suffix("").with_suffix(f".rcm.cache.{key_b}.json")
    assert cache_a.is_file()
    assert cache_b.is_file()

    combined = merge_submodel_fm_results(portfolio_path, merged.manifest)
    assert "Houtrib::FM-001" in combined
    assert "Roggebot::FM-002" in combined
