"""Tests voor library_distill (ADR-0009, grill 4)."""

from __future__ import annotations

from rcm_core.config import RCMConfig
from rcm_core.library_distill import (
    cluster_for_bibliotheek,
    distill_faalwijze_entry,
    distill_project_catalog,
    fm_technical_fingerprint,
    merge_catalog_to_bibliotheek,
    normalize_omschrijving,
    params_within_tolerance,
)
from rcm_core.models import AgingDistribution, Faalwijze, FailureType, RCMProject


def _fm(
    fm_id: str,
    *,
    omschrijving: str = "Lekkage",
    mttf: float = 25.0,
    sigma: float = 0.0,
) -> Faalwijze:
    return Faalwijze(
        fm_id=fm_id,
        pbs_id="P1",
        functie_id="F1",
        faalwijze_omschrijving=omschrijving,
        failure_type=FailureType.AGING,
        mttf_jaar=mttf,
        sigma_jaar=sigma,
        aging_distribution=AgingDistribution.NORMAL,
    )


def test_normalize_omschrijving_strips_punct() -> None:
    assert normalize_omschrijving("  Lekkage, (corrosie)! ") == "lekkage corrosie"


def test_fingerprint_stable_for_same_fm() -> None:
    cfg = RCMConfig()
    fm = _fm("FM-1")
    assert fm_technical_fingerprint(fm, cfg) == fm_technical_fingerprint(fm, cfg)


def test_fingerprint_differs_when_omschrijving_differs() -> None:
    cfg = RCMConfig()
    a = _fm("FM-1", omschrijving="Lekkage")
    b = _fm("FM-2", omschrijving="Slijtage")
    assert fm_technical_fingerprint(a, cfg) != fm_technical_fingerprint(b, cfg)


def test_fingerprint_same_for_different_mttf_same_omschrijving() -> None:
    cfg = RCMConfig()
    a = _fm("FM-1", mttf=25.0)
    b = _fm("FM-2", mttf=40.0)
    assert fm_technical_fingerprint(a, cfg) == fm_technical_fingerprint(b, cfg)


def test_distill_catalog_one_entry_per_fm() -> None:
    project = RCMProject(
        config=RCMConfig(),
        faalwijzes={"FM-1": _fm("FM-1"), "FM-2": _fm("FM-2", omschrijving="Slijtage")},
    )
    catalog = distill_project_catalog(
        project,
        source_id="houtrib",
        netwerkschakel="Houtrib",
        relative_path="Houtrib/x.rcm.json",
    )
    assert len(catalog) == 2
    assert {e.provenance.fm_id for e in catalog} == {"FM-1", "FM-2"}


def test_bibliotheek_merge_same_fingerprint_and_params() -> None:
    cfg = RCMConfig()
    fm_a = _fm("FM-A", omschrijving="Lekkage type A")
    fm_b = _fm("FM-B", omschrijving="LEKKAGE — type A!!!")
    e1 = distill_faalwijze_entry(
        fm=fm_a,
        config=cfg,
        source_id="s1",
        netwerkschakel="Houtrib",
        relative_path="Houtrib/a.rcm.json",
    )
    e2 = distill_faalwijze_entry(
        fm=fm_b,
        config=cfg,
        source_id="s2",
        netwerkschakel="Roggebot",
        relative_path="Roggebot/b.rcm.json",
    )
    assert e1.fingerprint == e2.fingerprint

    bib = merge_catalog_to_bibliotheek([e1, e2])
    assert len(bib) == 1
    item = next(iter(bib.values()))
    assert len(item.provenance) == 2


def test_bibliotheek_variant_cluster_on_param_mismatch() -> None:
    cfg = RCMConfig()
    e1 = distill_faalwijze_entry(
        fm=_fm("FM-1", mttf=25.0),
        config=cfg,
        source_id="s1",
        netwerkschakel="A",
        relative_path="A/x.rcm.json",
    )
    e2 = distill_faalwijze_entry(
        fm=_fm("FM-2", mttf=40.0, omschrijving="Lekkage"),
        config=cfg,
        source_id="s2",
        netwerkschakel="B",
        relative_path="B/x.rcm.json",
    )
    # Zelfde genormaliseerde omschrijving → zelfde fingerprint
    assert e1.fingerprint == e2.fingerprint
    assert not params_within_tolerance(e1.params, e2.params)

    clusters = cluster_for_bibliotheek([e1, e2])
    assert len(clusters) == 1
    assert clusters[0].variant_cluster is True

    bib = merge_catalog_to_bibliotheek([e1, e2])
    assert len(bib) == 2
