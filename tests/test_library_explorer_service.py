"""Tests voor library_explorer_service (slice 64 issue 04)."""

from __future__ import annotations

from rcm_core.models import BibliotheekItem
from rcm_desktop.adapter.library_explorer_service import build_library_explorer_rows


def test_row_shows_provenance_count_badge() -> None:
    item = BibliotheekItem(
        bibliotheek_id="DIST-abc",
        categorie="faalmodel",
        omschrijving="Lekkage",
        waarde="MTTF=10 jr",
        bron="2 bron(nen)",
        provenance=[
            {"source_id": "a", "netwerkschakel": "Houtrib", "fm_id": "FM-1", "relative_path": "a.rcm.json"},
            {"source_id": "b", "netwerkschakel": "Roggebot", "fm_id": "FM-1", "relative_path": "b.rcm.json"},
        ],
    )
    rows = build_library_explorer_rows({"DIST-abc": item})
    assert rows[0].bron_badge == "2 bronnen"
    assert rows[0].provenance_count == 2


def test_row_marks_variant_cluster() -> None:
    item = BibliotheekItem(
        bibliotheek_id="DIST-abc-V1",
        categorie="faalmodel",
        omschrijving="Lekkage",
        waarde="MTTF=10 jr",
        bron="Roggebot",
        toelichting="variant cluster (params wijken binnen fingerprint)",
        provenance=[{"source_id": "a", "netwerkschakel": "Roggebot", "fm_id": "FM-1", "relative_path": "x"}],
    )
    rows = build_library_explorer_rows({"DIST-abc-V1": item})
    assert rows[0].variant_cluster is True


def test_rows_sorted_by_omschrijving() -> None:
    bib = {
        "B": BibliotheekItem("B", "faalmodel", "Zebra", "", ""),
        "A": BibliotheekItem("A", "faalmodel", "Alpha", "", ""),
    }
    rows = build_library_explorer_rows(bib)
    assert [r.omschrijving for r in rows] == ["Alpha", "Zebra"]
