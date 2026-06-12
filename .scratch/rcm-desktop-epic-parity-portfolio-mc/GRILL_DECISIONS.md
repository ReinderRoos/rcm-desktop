# Grill-besluiten — Parity / Portfolio / Monte Carlo

**Datum:** 2026-06-05  
**Status:** besluiten 1–5 vast; **4+5 geïmplementeerd in PR0** (ADR-0009); **1 geïmplementeerd in slice 65** (ADR-0008)

## 1. Parity-drempel — **vast**

**Besluit:** AW-onzekerheidsband is voldoende; geen extra portfolio-€-drempel in v1.

| Metriek | Pass-criterium |
|---------|----------------|
| `total_cost_eur` | \|Δ\| ≤ `TotalCostErrAbs` **of** ≤ `TotalCostErrPc` × AW-waarde (welke AW levert) |
| Overige FM-metrieken | Zelfde patroon waar AW kolom + err% bestaat; anders **informatief** (geen fail) |
| Portfolio-totaal | Som FM-verdicts + optionele Project-sheet regel; **geen** extra absolute €-gate |

**Implicatie slice 57:** spike inventariseert welke err-kolommen AW exporteert; parity-service implementeert alleen wat in data zit.

---

## 2. Lifecycle / modeljaar bij merge — **vast**

**Besluit:** **Per netwerkschakel behouden**, met expliciete waarschuwing in wizard + manifest.

- Elk submodel behoudt eigen `lifecycle_years` en `modeljaar` in `PortfolioManifest.sources[]`.
- Portfolio-`RCMConfig` op root: alleen **weergave-defaults** (bijv. langste lifecycle voor LCC-as) — geen stille overschrijving van submodel-config.
- Validator/wizard waarschuwingen:
  - `WARN_LIFECYCLE_MISMATCH` — lifecycle verschilt > X% tussen schakels
  - `WARN_MODELJAAR_MISMATCH` — modeljaar verschilt tussen schakels
- LCC/aggregatie over portfolio: label “mixed horizon” of filter per netwerkschakel (ADR-0009).

---

## 3. Monte Carlo scope v1 — **vast**

**Besluit:** **Zoveel mogelijk** — volledige FM-lifecycle-stochastiek, analoog aan AW MC-run.

**Fase-indeling (performance-guard):**

| Fase | Scope | Prioriteit |
|------|--------|------------|
| **59-PR1** | Faalmomenten + CM + leeftijd/repair-quality; alle `aging_distribution`-varianten | Must |
| **59-PR2** | PM/REV/CN in MC-pad + task-group dedup (parity met analytisch) | Must |
| **59-PR3** | Cost/downtime-onzekerheid uit `import_settings` (`TotalCostErrPc`, …) | Should |
| **59-PR4** | Gevolgkosten / effect-sampling | Could (alleen als AW-kolommen + spike bevestigen) |

**SSOT:** analytisch blijft default run; MC opt-in. `FMMCResult` naast `FMResult`, aparte cache-namespace.

**Acceptatie:** seeded parity MC vs analytisch waar deterministisch; MC binnen AW-band waar import_settings benchmark heeft.

---

## 4. Library dedup — **advies**

**Aanbeveling: twee lagen — bronregistratie altijd; samenvoegen alleen op technische fingerprint.**

### Laag A — `DistilledFMEntry` (catalogus, geen model-mutatie)

Elke FM uit elk submodel → **eigen catalogusregel** met provenance:

```text
DistilledFMEntry
  catalog_id:     hash-based (stabiel)
  fingerprint:    technisch (zie onder)
  display_label:  genormaliseerde omschrijving + componenthint
  bronnen:        [{netwerkschakel, project_path, fm_id, pbs_path}]
  params:         {failure_type, mttf, sigma, beta, distribution, cost_cm, …}
```

Portfolio-FM's worden **niet** automatisch gemerged — traceerbaarheid gaat voor uniformiteit.

### Laag B — `BibliotheekItem` (herbruikbare aannames)

**Fingerprint (v1, conservatief):**

```text
hash(
  failure_type,
  aging_distribution,
  round(beta_jaar, 2),
  normalize(omschrijving)
)
```

MTTF/σ worden apart vergeleken via ``params_within_tolerance`` (Laag B).

| Situatie | Gedrag |
|----------|--------|
| Zelfde fingerprint, zelfde params | **Eén** `BibliotheekItem`; `bronnen[]` uitbreiden |
| Zelfde fingerprint, params wijken > drempel (MTTF >5%, σ >10%) | **Aparte** entries + UI-flag “variant cluster” |
| Alleen omschrijving lijkt op elkaar | **Niet** dedupen — alleen fuzzy **suggestie** in explorer |

**Waarom:** technische params zijn objectief; omschrijvingen variëren per analist/AW-import. Automatisch merge op tekst geeft valse uniformiteit.

**UI:** Library explorer toont “N bronnen” badge; drill-down naar per-schakel FM; handmatige “promote to library” blijft bestaande `sla_op_als_bibliotheek`-flow.

**Schema:** extend `BibliotheekItem` met optioneel `provenance: list[{source_id, fm_id, path}]` — pass-through compat (ADR-0004-stijl).

---

## 5. Server-pad — **advies**

**Aanbeveling v1: lokale map-only (SharePoint/OneDrive sync), geen SMB/REST in productie.**

### v1 — `PortfolioScanRoot` (wizard)

1. Gebruiker kiest **één root-map** via `QFileDialog` (bestaand patroon).
2. Scanner: max **diepte 2** — root → netwerkschakel-mappen → `.rcm.json` of `RCMCostdata export_*.xlsx`.
3. Security:
   - `Path.resolve()` + assert `resolved.is_relative_to(root.resolve())`
   - Alleen `.rcm.json`, `.xlsx` extensies; max bestandsgrootte (bijv. 50 MB)
   - Geen symlinks volgen
   - Geen paden buiten root in manifest opslaan tenzij gebruiker opt-in “bewaar volledig pad”
4. Manifest slaat op: `{relative_path, netwerkschakel_label, sha256, mtime, source_type}` — geen credentials.

### v1.5 — optioneel “manifest herladen”

Portfolio opgeslagen als `.rcm.json` + `portfolio_manifest.json` sidecar; heropen zonder rescan als bronbestanden ongewijzigd (hash-check).

### v2 — SMB/SharePoint REST (later, apart ADR)

| Optie | Advies |
|-------|--------|
| SMB UNC (`\\server\share`) | **Niet v1** — auth/complexiteit; gebruiker mapt sync-lokaal |
| Graph API / SharePoint REST | **v2** — OAuth, tenant-config, geen wachtwoorden in app; read-only scope |
| Geïndexeerde catalogus (JSON op server) | **Alternatief v2** — IT levert `portfolio-index.json` met relatieve paden; app blijft lokaal lezen |

**Praktisch voor MNN BAP:** `5_RWS_MNN_Lelystad_BAP` als sync-map is v1-voldoende; wizard auto-detecteert Houtrib/Roggebot/… op foldernaam + optionele `netwerkschakel.yaml` override per map.

---

## Volgorde (ongewijzigd)

1. **Slice 65** — RCM-Cost parity (ADR-0008) ✓
2. **Slice 64** — merge + manifest (ADR-0009) ✓
3. **Slice 59-MC** — Monte Carlo FM (ADR-0010) — *niet verwarren met slice 59 FM-editor*

## Open na deze grill

- [ ] Spike Roggebot: welke AW benchmark-kolommen naast `TotalCostErrPc`?
- [ ] Slice-nummering hernoemen in PRD (57-parity / 63-portfolio / 64-mc?) om collision met bestaande slices te vermijden
