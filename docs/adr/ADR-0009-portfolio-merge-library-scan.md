# ADR-0009: Portfolio-merge, faalwijze-library en lokale map-scan

**Status:** accepted  
**Date:** 2026-06-05  
**Parent:** epic parity/portfolio/MC; grill-sessie 2026-06-05; slice **64** (portfolio-merge)

## Context

Organisaties (o.a. MNN Lelystad BAP) hebben tientallen RCM-Cost-modellen per
netwerkschakel. Doelen:

1. Modellen naast elkaar onder één fictieve top-event (PBS) met traceerbare provenance.
2. Submodellen **apart** doorgerekend (performance, cache-partitionering — latere issue).
3. Faalwijze-**catalogus** destilleren met bronvermeldingen; uniformiteit **controleren**,
   niet stil samenvoegen.

Grill-besluiten (2, 4, 5) bepalen lifecycle, library-dedup en server-pad.

## Decision

### Lifecycle / modeljaar (grill 2)

- Elk submodel behoudt eigen `lifecycle_years` en `modeljaar` in `PortfolioManifest.sources[]`.
- Portfolio-root-`RCMConfig`: alleen weergave-defaults; **geen** stille overschrijving.
- Wizard/manifest waarschuwingen: `WARN_LIFECYCLE_MISMATCH`, `WARN_MODELJAAR_MISMATCH`.
- LCC over portfolio: label “mixed horizon” of filter per netwerkschakel.

### Library dedup — twee lagen (grill 4)

**Laag A — catalogus (`DistilledFMEntry`, `library_distill.py`)**

- Eén catalogusregel **per FM per bron**; portfolio-FM's worden niet auto-gemerged.
- Technische **fingerprint** voor clustering en Laag B; geen dedup op omschrijving alleen.

**Laag B — bibliotheek (`BibliotheekItem`)**

- Fingerprint = semantisch cluster (`failure_type`, `aging_distribution`, `β`, genormaliseerde omschrijving).
- MTTF/σ match via `params_within_tolerance` (≤5% / ≤10%).
- Zelfde fingerprint + match → één item, `provenance[]` uitbreiden.
- Zelfde fingerprint + mismatch → aparte items + “variant cluster” (UI later).

**Schema:** optioneel `BibliotheekItem.provenance: list[{source_id, netwerkschakel, fm_id, relative_path}]`
— pass-through compat (ADR-0004-stijl).

### Server-pad v1 — lokale map-only (grill 5)

- Gebruiker kiest **sync-root** via bestaande file-dialog; geen SMB/REST in v1.
- Scanner (`portfolio_scan.py`): diepte root → netwerkschakel-map → `.rcm.json` /
  `RCMCostdata export_*.xlsx`; max diepte **2**; max bestand **50 MB**.
- Security: `Path.resolve()`, pad binnen root, geen symlinks volgen, extensie-whitelist.
- Manifest: `relative_path`, `sha256`, `mtime`, `netwerkschakel_label` — **geen** credentials.
- Volledige absolute paden alleen met expliciete opt-in `store_absolute_paths`.
- v2 (Graph API / portfolio-index.json): **out of scope**; apart ADR.

### ID-prefix (merge)

- `{NETWERKSCHAKEL}::{orig_id}` voor FM/PBS/PM/… — traceerbaar, geen collisions.
- `PortfolioManifest.id_map` bewaart orig → merged mapping.

### Manifest-opslag

- Sidecar `portfolio_manifest.json` naast portfolio `.rcm.json` (v1.5 herladen zonder rescan).
- Optioneel mirror onder `import_settings["portfolio_manifest"]` na normalisatie (pass-through).

## Consequences

- Qt-vrije modules: `portfolio_manifest`, `portfolio_scan`, `library_distill`; merge-motor volgt in slice 64 issues 02+.
- Desktop-wizard consumeert scan-resultaat; geen netwerkcode in v1.
- Bestaande `.rcm.json` zonder manifest blijven geldig.
- SMB/SharePoint REST vereist nieuw ADR vóór implementatie.

## References

- `rcm_core/portfolio_manifest.py`
- `rcm_core/portfolio_scan.py`
- `rcm_core/library_distill.py`
- `.scratch/rcm-desktop-epic-parity-portfolio-mc/GRILL_DECISIONS.md`
