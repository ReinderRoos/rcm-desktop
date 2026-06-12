"""Faalwijze-catalogus destilleren + bibliotheek-dedup op fingerprint (ADR-0009, grill 4)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from rcm_core.config import RCMConfig
from rcm_core.models import BibliotheekItem, Faalwijze, RCMProject

MTTF_REL_TOLERANCE = 0.05
SIGMA_REL_TOLERANCE = 0.10
_OMSCHR_MAX_LEN = 80
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class FMProvenanceRef:
    """Bronverwijzing voor catalogus of bibliotheek."""

    source_id: str
    netwerkschakel: str
    fm_id: str
    relative_path: str
    pbs_id: str = ""

    def to_dict(self) -> dict[str, str]:
        out = {
            "source_id": self.source_id,
            "netwerkschakel": self.netwerkschakel,
            "fm_id": self.fm_id,
            "relative_path": self.relative_path,
        }
        if self.pbs_id:
            out["pbs_id"] = self.pbs_id
        return out

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> FMProvenanceRef:
        return cls(
            source_id=str(d.get("source_id") or ""),
            netwerkschakel=str(d.get("netwerkschakel") or ""),
            fm_id=str(d.get("fm_id") or ""),
            relative_path=str(d.get("relative_path") or ""),
            pbs_id=str(d.get("pbs_id") or ""),
        )


@dataclass(frozen=True)
class DistilledFMParams:
    failure_type: str
    mttf_jaar: float
    sigma_jaar: float
    aging_distribution: str
    beta_jaar: float
    cost_cm_eur: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure_type": self.failure_type,
            "mttf_jaar": self.mttf_jaar,
            "sigma_jaar": self.sigma_jaar,
            "aging_distribution": self.aging_distribution,
            "beta_jaar": self.beta_jaar,
            "cost_cm_eur": self.cost_cm_eur,
        }


@dataclass(frozen=True)
class DistilledFMEntry:
    """Laag A — één catalogusregel per FM per bron (geen auto-merge in model)."""

    catalog_id: str
    fingerprint: str
    display_label: str
    provenance: FMProvenanceRef
    params: DistilledFMParams
    normalized_omschrijving: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "fingerprint": self.fingerprint,
            "display_label": self.display_label,
            "provenance": self.provenance.to_dict(),
            "params": self.params.to_dict(),
            "normalized_omschrijving": self.normalized_omschrijving,
        }


@dataclass
class BibliotheekMergeCluster:
    """Laag B — gegroepeerde entries voor één bibliotheekitem."""

    fingerprint: str
    entries: list[DistilledFMEntry] = field(default_factory=list)
    variant_cluster: bool = False

    @property
    def representative(self) -> DistilledFMEntry:
        return self.entries[0]


def normalize_omschrijving(text: str, *, max_len: int = _OMSCHR_MAX_LEN) -> str:
    lowered = text.casefold().strip()
    collapsed = _NON_ALNUM.sub(" ", lowered).strip()
    if len(collapsed) > max_len:
        return collapsed[:max_len]
    return collapsed


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def fm_technical_fingerprint(
    fm: Faalwijze,
    config: RCMConfig,
) -> str:
    """Semantische fingerprint voor clustering (grill 4).

    MTTF/sigma zitten in ``DistilledFMParams`` voor tolerantie-check;
    niet in de hash — anders geen variant clusters bij dezelfde omschrijving.
    """
    del config  # API-symmetrie; sigma niet in fingerprint
    payload = {
        "failure_type": fm.failure_type.value,
        "aging_distribution": fm.aging_distribution.value,
        "beta_jaar": round(fm.beta_jaar, 2),
        "normalized_omschrijving": normalize_omschrijving(fm.faalwijze_omschrijving),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return _sha256_hex(canonical)


def fm_params_from_faalwijze(fm: Faalwijze, config: RCMConfig) -> DistilledFMParams:
    return DistilledFMParams(
        failure_type=fm.failure_type.value,
        mttf_jaar=fm.mttf_jaar,
        sigma_jaar=fm.effective_sigma(config.default_sigma_fraction),
        aging_distribution=fm.aging_distribution.value,
        beta_jaar=fm.beta_jaar,
        cost_cm_eur=fm.cost_cm_eur,
    )


def params_within_tolerance(
    a: DistilledFMParams,
    b: DistilledFMParams,
    *,
    mttf_rel: float = MTTF_REL_TOLERANCE,
    sigma_rel: float = SIGMA_REL_TOLERANCE,
) -> bool:
    if a.failure_type != b.failure_type:
        return False
    if a.aging_distribution != b.aging_distribution:
        return False
    if abs(a.beta_jaar - b.beta_jaar) > 0.01:
        return False

    def _rel_close(x: float, y: float, tol: float) -> bool:
        if x == 0.0 and y == 0.0:
            return True
        base = max(abs(x), abs(y), 1e-9)
        return abs(x - y) / base <= tol

    return _rel_close(a.mttf_jaar, b.mttf_jaar, mttf_rel) and _rel_close(
        a.sigma_jaar, b.sigma_jaar, sigma_rel
    )


def distill_faalwijze_entry(
    *,
    fm: Faalwijze,
    config: RCMConfig,
    source_id: str,
    netwerkschakel: str,
    relative_path: str,
) -> DistilledFMEntry:
    fingerprint = fm_technical_fingerprint(fm, config)
    catalog_id = _sha256_hex(f"{source_id}::{fm.fm_id}")
    norm = normalize_omschrijving(fm.faalwijze_omschrijving)
    label = fm.faalwijze_omschrijving.strip() or fm.fm_id
    return DistilledFMEntry(
        catalog_id=catalog_id,
        fingerprint=fingerprint,
        display_label=label,
        provenance=FMProvenanceRef(
            source_id=source_id,
            netwerkschakel=netwerkschakel,
            fm_id=fm.fm_id,
            relative_path=relative_path,
            pbs_id=fm.pbs_id,
        ),
        params=fm_params_from_faalwijze(fm, config),
        normalized_omschrijving=norm,
    )


def distill_project_catalog(
    project: RCMProject,
    *,
    source_id: str,
    netwerkschakel: str,
    relative_path: str,
) -> list[DistilledFMEntry]:
    """Laag A: één entry per FM — geen samenvoeging."""
    return [
        distill_faalwijze_entry(
            fm=fm,
            config=project.config,
            source_id=source_id,
            netwerkschakel=netwerkschakel,
            relative_path=relative_path,
        )
        for fm in project.faalwijzes.values()
    ]


def cluster_for_bibliotheek(
    catalog: list[DistilledFMEntry],
) -> list[BibliotheekMergeCluster]:
    """Laag B: groepeer op fingerprint; markeer variant clusters bij param-mismatch."""
    by_fp: dict[str, list[DistilledFMEntry]] = {}
    for entry in catalog:
        by_fp.setdefault(entry.fingerprint, []).append(entry)

    clusters: list[BibliotheekMergeCluster] = []
    for fingerprint, entries in sorted(by_fp.items(), key=lambda kv: kv[0]):
        variant = False
        rep = entries[0].params
        for other in entries[1:]:
            if not params_within_tolerance(rep, other.params):
                variant = True
                break
        clusters.append(
            BibliotheekMergeCluster(
                fingerprint=fingerprint,
                entries=entries,
                variant_cluster=variant,
            )
        )
    return clusters


def _provenance_from_entry(entry: DistilledFMEntry) -> dict[str, str]:
    return entry.provenance.to_dict()


def bibliotheek_item_from_cluster(
    cluster: BibliotheekMergeCluster,
    *,
    bibliotheek_id_prefix: str = "DIST",
) -> BibliotheekItem | list[BibliotheekItem]:
    """Maak BibliotheekItem(s) uit cluster; split bij variant_cluster."""
    if cluster.variant_cluster:
        items: list[BibliotheekItem] = []
        for idx, entry in enumerate(cluster.entries, start=1):
            bib_id = f"{bibliotheek_id_prefix}-{entry.fingerprint[:12]}-V{idx}"
            p = entry.params
            items.append(
                BibliotheekItem(
                    bibliotheek_id=bib_id,
                    categorie="faalmodel",
                    omschrijving=entry.display_label,
                    waarde=(
                        f"MTTF={p.mttf_jaar:.1f} jr, σ={p.sigma_jaar:.2f} jr, "
                        f"{p.aging_distribution}"
                    ),
                    bron=entry.provenance.netwerkschakel,
                    toelichting="variant cluster (params wijken binnen fingerprint)",
                    provenance=[_provenance_from_entry(entry)],
                )
            )
        return items

    entry = cluster.representative
    p = entry.params
    provenance = [_provenance_from_entry(e) for e in cluster.entries]
    bib_id = f"{bibliotheek_id_prefix}-{cluster.fingerprint[:12]}"
    return BibliotheekItem(
        bibliotheek_id=bib_id,
        categorie="faalmodel",
        omschrijving=entry.display_label,
        waarde=(
            f"MTTF={p.mttf_jaar:.1f} jr, σ={p.sigma_jaar:.2f} jr, "
            f"{p.aging_distribution}"
        ),
        bron=f"{len(provenance)} bron(nen)",
        toelichting="",
        provenance=provenance,
    )


def merge_catalog_to_bibliotheek(
    catalog: list[DistilledFMEntry],
    existing: Mapping[str, BibliotheekItem] | None = None,
    *,
    bibliotheek_id_prefix: str = "DIST",
) -> dict[str, BibliotheekItem]:
    """Bouw bibliotheek-dict uit gedistilleerde catalogus (Laag B)."""
    out: dict[str, BibliotheekItem] = dict(existing or {})
    for cluster in cluster_for_bibliotheek(catalog):
        made = bibliotheek_item_from_cluster(
            cluster, bibliotheek_id_prefix=bibliotheek_id_prefix
        )
        if isinstance(made, list):
            for item in made:
                out[item.bibliotheek_id] = item
        else:
            existing_item = out.get(made.bibliotheek_id)
            if existing_item is not None and not cluster.variant_cluster:
                merged_prov = list(existing_item.provenance)
                seen = {json.dumps(p, sort_keys=True) for p in merged_prov}
                for ref in made.provenance:
                    key = json.dumps(ref, sort_keys=True)
                    if key not in seen:
                        merged_prov.append(ref)
                        seen.add(key)
                out[made.bibliotheek_id] = BibliotheekItem(
                    bibliotheek_id=made.bibliotheek_id,
                    categorie=made.categorie,
                    omschrijving=made.omschrijving,
                    waarde=made.waarde,
                    bron=f"{len(merged_prov)} bron(nen)",
                    toelichting=made.toelichting,
                    provenance=merged_prov,
                )
            else:
                out[made.bibliotheek_id] = made
    return out
