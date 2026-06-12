"""Library explorer rijen uit portfolio-bibliotheek (slice 64 issue 04)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import BibliotheekItem


@dataclass(frozen=True)
class LibraryExplorerRow:
    bibliotheek_id: str
    omschrijving: str
    categorie: str
    waarde: str
    bron_badge: str
    provenance_count: int
    variant_cluster: bool
    provenance: tuple[dict[str, str], ...]


def _is_variant_cluster(item: BibliotheekItem) -> bool:
    hint = (item.toelichting or "").casefold()
    if "variant cluster" in hint:
        return True
    return "-V" in item.bibliotheek_id


def _bron_badge(item: BibliotheekItem) -> tuple[str, int]:
    count = len(item.provenance)
    if count > 1:
        return f"{count} bronnen", count
    if count == 1:
        net = item.provenance[0].get("netwerkschakel") or item.bron or "1 bron"
        return str(net), 1
    return item.bron or "—", 0


def build_library_explorer_rows(
    bibliotheek: dict[str, BibliotheekItem],
) -> list[LibraryExplorerRow]:
    rows: list[LibraryExplorerRow] = []
    for item in bibliotheek.values():
        badge, count = _bron_badge(item)
        rows.append(
            LibraryExplorerRow(
                bibliotheek_id=item.bibliotheek_id,
                omschrijving=item.omschrijving,
                categorie=item.categorie,
                waarde=item.waarde,
                bron_badge=badge,
                provenance_count=count,
                variant_cluster=_is_variant_cluster(item),
                provenance=tuple(dict(p) for p in item.provenance),
            )
        )
    return sorted(rows, key=lambda r: (r.categorie, r.omschrijving.casefold()))
