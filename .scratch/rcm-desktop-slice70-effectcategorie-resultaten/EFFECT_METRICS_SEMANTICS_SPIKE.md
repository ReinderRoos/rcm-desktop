# Effect-metrics semantics spike — slice 70

**Datum:** 2026-06-05  
**Status:** **Leidend** (HITL grill-with-docs afgerond)  
**Parent:** slice 70 issue 01 + issue 11 (HITL-deel)  
**Brondata:** `tests/fixtures/RCMCostdata export_CM.xlsx`; golden cause `06H-350.1.1.1.1.1.A.1`  
**Vocabulaire:** `CONTEXT.md` sectie *Effectimpact*

---

## 1. HITL-besluiten (samenvatting)

| # | Onderwerp | Besluit |
|---|-----------|---------|
| 1 | **Waarde per effectklasse** | **C — categorie-specifiek** |
| 2 | **Motor normalisatie (issue 02)** | **A — split raw** (`fm_effect_bijdragen` + `pm_effect_bijdragen`) |
| 3 | **Taxonomie (issue 11 AFK)** | **B — genormaliseerd + AW-type bewaren** |
| 4 | **Gevolgkosten-import** | **A — ADR-0004 handhaven** (geen `CostPerOccurrence`) |
| 5 | **Top 10 UX (issues 04–05)** | **D — hybride** (bron Effectklasse → metric Effectimpact) |
| 6 | **AW-pariteit (issues 10, 12)** | **B — informatief, geen gate** |

Issues **02–05** en **11 AFK** mogen starten. Issue **01** gate is opgeheven.

---

## 2. Besluit 1 — Categorie-specifieke metrics

### 2.1 Presentatie per effectcategorie

| Effectcategorie | CM-deel (motor raw) | Presentatie (`EffectImpactService`) | UI-label |
|-----------------|---------------------|-------------------------------------|----------|
| **beschikbaarheid** | incidenten-equivalent | `RF × downtime_per_failure × expected_failures` uren + PM-uren | NB per effect (uren / %) |
| **veiligheid** | incidenten-equivalent | `expected_failures × RF` (ongewijzigd) | Veiligheidsincidenten |
| **kosten** | — | later / issue 10 informatief | — |
| **overig** | incidenten-equivalent | incidenten + waarschuwing | Effectimpact (incidenten) |

**Niet-beschikbaarheid (totaal)** blijft de default Top 10-metric bij bron Component/Faalwijze: totale CM + PM + verborgen NB-downtime (slice 33, ongewijzigd).

VGM heet **niet** “Niet-beschikbaarheid” in de UI.

### 2.2 RCM2 exposeert vs AWB-proxy

| Aspect | RCM2 (analytisch) | AWB (MC) | Pariteit |
|--------|-------------------|----------|----------|
| Beschikbaarheid per effect | RF-gewogen downtime-uren | `TotalTdt`-proxies / effect-downtime | Informatief Δ |
| Veiligheid per effect | RF-gewogen incidenten | faal/incident-proxies | Informatief Δ |
| EffectCost | alleen handmatig `cost_gevolg_eur` | `EffectCost` in benchmark | Informatief; geen RCM2-euro zonder gevolgkosten |

Volledige MC-pariteit per effect is **out of scope** (PRD user story 38).

---

## 3. Besluit 2 — Motor split raw (issue 02)

### 3.1 Huidige motor (pre-slice 70)

| Veld | CM | PM | Eenheid |
|------|----|----|---------|
| `effect_bijdragen` | `expected_failures × RF` | `duration × RF × executions` | **gemengd** |
| `effect_bijdragen_per_jaar` | `faalmomenten[h] × RF` | PM-lifecycle / buckets | **gemengd** |

### 3.2 Na issue 02

| Veld | Inhoud | Eenheid |
|------|--------|---------|
| `fm_effect_bijdragen` | per klasse: `expected_failures × RF` | incidenten-equivalent |
| `pm_effect_bijdragen` | per klasse: `duration × RF × executions` | uren |
| `effect_bijdragen` | som CM + PM per klasse | **deprecated mixed** — alleen backward-compat; UI gebruikt split |

`EffectImpactService` is enige plek die categorie-formules toepast. Geen normalisatie naar uren in de motor (verworpen optie B).

**Cache:** bump `CACHE_INPUTS_VERSION` wanneer serialisatie/FM-hash nieuwe velden bevat.

---

## 4. Besluit 3 — Taxonomie (issue 11 AFK)

### 4.1 Model

| Veld | Bron | Doel |
|------|------|------|
| `EffectKlasse.categorie` | genormaliseerd uit AW `Type` | metrics, filters, Top 10 |
| `EffectKlasse.aw_effect_type` *(nieuw)* | ruwe `RcmEffects.Type` | traceerbaarheid, AW-vergelijking |

Pass-through van `Type` → `categorie` wordt vervangen door mapping.

### 4.2 Mapping-tabel v1

| AW `Type` | `categorie` | Metric bij Effectimpact |
|-----------|-------------|-------------------------|
| `Schutten`, `Keren`, `Kruisen`, `Spuien` | `beschikbaarheid` | NB per effect (uren) |
| `VGM` | `veiligheid` | Veiligheidsincidenten |
| *(leeg)* / onbekend | `overig` | incidenten + import-waarschuwing |
| expliciet kosten-type *(indien later)* | `kosten` | informatief (issue 10) |

Onbekende types → `overig` + waarschuwing `Onbekend AW effecttype: …`.

---

## 5. Besluit 4 — Gevolgkosten (issue 11 HITL)

**ADR-0004 blijft:** geen import van `CostPerOccurrence` → `cost_gevolg_eur`.

- `cost_gevolg_eur` blijft `0.0` na import.
- Handmatig instelbaar via FM-editor (slice 44).
- AW `EffectCost` per cause blijft in `import_settings` voor informatieve pariteit.

---

## 6. Besluit 5 — Top 10 hybride (issues 04–05)

| Bron | Default metric | Gedrag |
|------|----------------|--------|
| Component / Faalwijze | **Niet-beschikbaarheid (totaal)** | ongewijzigd slice 33 |
| **Effectklasse** | **Effectimpact** | auto-switch bij bronwissel |

Bij bron Effectklasse:

- Rijen = effectklassen (Pareto).
- Kolom eenheid/label per rij afhankelijk van `categorie`.
- Optionele filter: all / beschikbaarheid / veiligheid / overig.
- RF zichtbaar in tooltip of subkolom.

Nieuwe workspace-constanten: `SOURCE_EFFECTKLASSE`, `METRIC_EFFECTIMPACT`.

---

## 7. Besluit 6 — AW-pariteit informatief (issues 10, 12)

### 7.1 Modelcontrole AW (uitbreiding)

| Effectcategorie | RCM2 | AW benchmark | Gate v1 |
|-----------------|------|--------------|---------|
| beschikbaarheid | NB per effect (uren) | downtime/Tdt waar beschikbaar | **Nee** |
| veiligheid | incidenten-equivalent | incident-proxies | **Nee** |
| alle | — | `EffectCost` | **Nee** (informatief) |

Verdict-labels: pass / informative / missing (ADR-0008-stijl). **Geen fail** op effect-niveau in v1.

### 7.2 Validatie-export tab Effectcategorieën (issue 12)

Kolommen: FM, effectklasse, categorie, RCM2-waarde, eenheid, AW-waarde (indien), Δ, cause codes.

| Code | Betekenis |
|------|-----------|
| **E1** | import/link (slice 69) |
| **E2** | metrics/eenheid (analytisch vs MC, categorie-mismatch) |
| **E3** | ontbrekende AW-benchmark |

---

## 8. Golden-cause walkthrough — `06H-350.1.1.1.1.1.A.1`

**Omschrijving:** Drukverlies door breuk slangen; MTTF=25 jr; slice 69 import bevestigd.

### 8.1 FM-effectlinks (CM-fixture)

| Effectklasse | RF | AW type → categorie |
|--------------|-----|---------------------|
| VGM - Effect 3 | 0,1 | VGM → veiligheid |
| VGM - Effect 2 | 0,9 | VGM → veiligheid |
| Schutten 0-20% functieverlies | 1,0 | Schutten → beschikbaarheid |
| Schutten 81-100% functieverlies | 0,5 | Schutten → beschikbaarheid |

### 8.2 Motor raw (symbool)

Zij `F = expected_failures`, `D = downtime_per_failure.to_hours()`, REV-PM met `P_uren` PM-effecturen per klasse.

| Klasse | `fm_effect_bijdragen` | `pm_effect_bijdragen` |
|--------|----------------------|----------------------|
| VGM - Effect 3 | `0,1 × F` incidenten | `0,1 × P_uren` uren |
| VGM - Effect 2 | `0,9 × F` incidenten | `0,9 × P_uren` uren |
| Schutten 0-20% | `1,0 × F` incidenten | `1,0 × P_uren` uren |
| Schutten 81-100% | `0,5 × F` incidenten | `0,5 × P_uren` uren |

### 8.3 Presentatie na `EffectImpactService`

| Klasse | CM presentatie | PM presentatie | Totaal label |
|--------|----------------|----------------|--------------|
| VGM - Effect 3 | `0,1 × F` incidenten | PM-uren apart | Veiligheidsincidenten |
| VGM - Effect 2 | `0,9 × F` incidenten | PM-uren apart | Veiligheidsincidenten |
| Schutten 0-20% | `F × D` uren | PM-uren | NB per effect (uren) |
| Schutten 81-100% | `0,5 × F × D` uren | PM-uren | NB per effect (uren) |

### 8.4 Acceptatie slice 70 (issues 04–06, 13)

Na run op CM-fixture moet de analist **vier effectrijen** zien in Top 10 (bron Effectklasse) en FM-inspector, met RF 0,1 / 0,9 / 1,0 / 0,5 en correcte eenheid per categorie.

---

## 9. Deep module — `EffectImpactService` (issue 03)

Qt-vrij; input: `RCMProject` + `dict[str, FMResult]`.

```
aggregate(project, fm_results, *, scope, metric, horizon, presentation, categorie_filter?)
→ tuple[EffectImpactRow, ...]

EffectImpactRow:
  klasse_id, label, categorie, aw_effect_type, rf_display,
  waarde_cm, waarde_pm, waarde_totaal,
  eenheid, share_pct
```

Consumenten (geen eigen aggregatie): Top 10, inspector, KPI, rapport, validatie-export, parity.

---

## 10. ADR-verwijzingen

- **ADR-0004** — taxonomie + gevolgkosten-bevestiging (§ effect-taxonomie slice 70)
- **ADR-0008** — effect-pariteit informatief (§ effect-metrics slice 70)
- **Slice 69** — import link-logica ongewijzigd
