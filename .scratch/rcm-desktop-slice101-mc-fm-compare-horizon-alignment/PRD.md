# PRD — Slice 101: MC FM-presentatie op gelijke horizon

**Status:** done  
**Versie:** 1.0  
**Datum:** 2026-06-13  
**Triage:** `done`  
**Type:** Bugfix + presentatie-pariteit (adapter; geen schema-drift op `RCMProject`)  
**Parent:** slice 100 (scenario-workflow + MC P50-rollups); slice 98 (MC engine v1); slice 80 (FM presentation-scale voor analytisch)  
**Companion docs:** ADR-0018 (MC presentatie), ADR-0007 (scenario compare), CONTEXT.md (ContributionPresentation)  
**HILT-bron:** `.scratch/rcm-desktop-slice100-scenario-workflow-mc-rollups/HILT100_HANDCHECK.md` + post-fix analist-feedback (2026-06-13)

> Synthese van **HILT100 follow-up**: FM-vergelijking MC ↔ analytisch toont extreme
> verschillen (tot ~60×) terwijl Top 10/LCC na slice-100-fixes wél kloppen. Root cause:
> **presentatie-asymmetrie** — analytische FM-kolommen respecteren de gedeelde
> horizon-keuze (`ContributionPresentation`); MC FM-kolommen tonen altijd **lifecycle
> P50-totalen**. Met horizon **Levensduur** klopt de vergelijking; met default
> **Ø per jaar** niet. Deze slice maakt MC FM automatisch **horizon-conform**.

---

## Problem Statement

Slice 100 bracht **FM-resultaten compare** (split scenario 1 | scenario 2) en
**gemengde run-modus** (analytisch vs Monte Carlo). Analisten verwachten dat
beide kolommen dezelfde getallen betekenis geven — vergelijkbaar met Top 10 en
LCC, die al de gedeelde horizon-toolbar volgen.

Vandaag is dat voor FM **niet** het geval:

| Pad | Horizon-gedrag |
|-----|----------------|
| **Analytisch FM** (single-run + compare slot) | `apply_presentation_scale_to_fm_rows` schaalt faalmomenten, downtime/NB en kosten naar `snapshot.contribution_presentation` (default: **Ø per jaar**) |
| **MC FM** (single-run + compare slot) | Ruwe **lifecycle P50** uit `FMMCResultRow` — geen schaling |
| **Top 10 / LCC** (live + compare) | Gebruiken P50-rollup + bestaande horizon/bucket-logica (slice 100) |

Gevolg in HILT100 (Haarlem demo, default horizon):

- FM-compare MC vs analytisch: schijnbaar **50–60× verschil** op downtime/kosten
  per rij, terwijl dezelfde scenario's in Top 10/LCC **plausibel dichtbij** liggen.
- Analist moet handmatig horizon op **Levensduur** zetten om FM-compare te vertrouwen.
- Single-run MC FM-detail wijkt op dezelfde manier af van analytisch FM-detail
  bij dezelfde horizon-instelling (inconsistentie binnen één scherm).

Dit is **geen motor-bug** en geen inherent MC-discrete-effect (P50=2, P10=0):
de waarden kloppen wél wanneer beide kolommen dezelfde horizon gebruiken.
Het is een **presentatie-gap** in de adapter tussen MC band-rijen en de bestaande
`ContributionPresentation`-SSOT (slice 33/80).

### Waarom dit nu blokkeert

- **Scenariovergelijking** (slice 100 kernbelofte) verliest geloofwaardigheid op
  FM-niveau — precies waar analisten faalwijze-voor-faalwijze willen redeneren.
- **Mixed-mode compare** (S1 analytisch, S2 MC) is het meest gevoelig: twee
  semantieken naast elkaar zonder expliciete waarschuwing.
- Default UX (**Ø per jaar**) is de normale analisten-instelling; MC mag daar
  niet stilzwijgend lifecycle-totalen tonen.

---

## Solution

**Eén presentatieregel voor alle FM-kolommen:** MC P50-waarden (en band-tooltips)
door dezelfde horizon-/jaarkiezer-pipeline als analytische FM-rijen.

### Kernmechanisme

1. **Herbruik MC P50 → `FMResult`-rollup** (`fm_results_from_mc_p50`, slice 100)
   als tussenlaag — bevat lifecycle-totalen én `horizon_profile` voor bucket-schaal.
2. **Nieuwe adapter-helper** (naam TBD, bijv.
   `apply_presentation_scale_to_mc_rows`) die:
   - per `FMMCResultRow` de bijbehorende synthetische `FMResult` opzoekt;
   - `contribution_value_for_fm` / `kosten_scalar_for_fm` /
     `nb_scalar_for_fm` (via `effect_presentation_for_contribution`) toepast
     — **dezelfde functies als `apply_presentation_scale_to_fm_rows`**;
   - geschaalde P50 in de tabelkolom zet;
   - P10/P90 in tooltip **met dezelfde schaalfactor** transformeert (niet
     lifecycle-banden tonen terwijl kolom per-jaar is).
3. **Integratiepunten:**
   - `build_fm_detail_view` — MC-pad (`mc_bands`) na run;
   - `build_fm_detail_view_for_compare_slot` — MC compare-slot;
   - optioneel gecentraliseerd in één functie die beide aanroept.

### Gedrag per horizon (pariteit met slice 80)

| `ContributionPresentation` | Analytisch (huidig) | MC (na slice 101) |
|----------------------------|---------------------|-------------------|
| `horizon=lifecycle` | Lifecycle-totalen | Lifecycle P50 (≈ huidig gedrag) |
| `horizon=per_year`, `year_choice=average` | Ø per kalenderbucket | P50 geschaald naar jaargemiddelde |
| `horizon=per_year`, `year_choice=<jaar>` | Waarde in gekozen kalenderjaar | P50 geschaald naar dat jaar |
| NB-filter actief | `nb_scalar_for_fm` met filter | Idem op MC-synthetische `FMResult` |
| `unavailability_display` hours/percent | Via `EffectPresentation` | Idem |

### UX / labeling

- **Geen aparte MC-horizon-toggle** — MC volgt altijd `snapshot.contribution_presentation`
  (zelfde toolbar als Top 10/LCC/FM analytisch).
- **Kolomheaders** blijven MC P50 + band-tooltip (slice 98); tooltip toont
  **geschaalde** P10/P90 consistent met zichtbare kolomwaarde.
- **Geen extra waarschuwing** nodig wanneer horizons gelijk getrokken zijn;
  optioneel: subtiele horizon-hint in compare-chrome als beide slots MC/analytisch
  mixen (nice-to-have, niet blocking).

### RF-kolom (bekende asymmetrie)

MC `rf` en analytische `rf` (via `enrich_fm_rows_with_nmf_rf`) kunnen semantisch
verschillen. **Out of scope** voor deze slice — focus op faalmomenten, downtime,
kosten. RF blijft tonen zoals vandaag; geen schaal-claim op RF.

---

## User Stories

### FM single-run pariteit

1. As a reliability-analist, I want **MC FM-resultaten** to respect the same
   horizon toolbar as analytical FM, so that switching Run-modus does not change
   the meaning of column numbers without me noticing.
2. As a reliability-analist, I want MC P50 **Ø per jaar** when that horizon is
   selected, so that FM-detail matches Top 10 ranking for the same run.
3. As a reliability-analist, I want MC band tooltips (P10/P90) scaled to the
   active horizon, so that uncertainty bands are comparable to the displayed P50.

### FM scenario compare

4. As a reliability-analist, I want **both FM compare columns** to use the same
   horizon presentation automatically, so that I do not manually switch to
   Levensduur to trust mixed MC vs analytical compare.
5. As a reliability-analist, I want mixed-mode compare (S1 analytical, S2 MC)
   to show per-FM values on a **common basis** (same year or lifecycle), so that
   side-by-side differences reflect model choices not unit mismatch.
6. As a trainer, I want FM compare differences in default **Ø per jaar** mode
   to be in a plausible ratio (not ~60×) for the Haarlem demo, so that MC is
   explainable in workshops.

### Regressie / architectuur

7. As a developer, I want one adapter helper for MC presentation-scale reused
   by single-run and compare paths, so that slice 80 SSOT is not duplicated.
8. As a developer, I want tests that fail if MC rows bypass
   `ContributionPresentation` again, so that HILT100-class bugs do not recur.

---

## Technical Design

### Module boundaries

| Module | Wijziging |
|--------|-----------|
| **`simulation_engine_service`** | Geen motor-wijziging; `fm_results_from_mc_p50` blijft SSOT voor buckets |
| **`result_view_service`** of **`contribution_horizon_value_service`** | Nieuwe `apply_presentation_scale_to_mc_rows(...)` |
| **`workspace_view_service`** | MC-paden in `build_fm_detail_view` en `build_fm_detail_view_for_compare_slot` roepen scaler aan |
| **`fm_mc_results_table_model`** | Geen logica-wijziging indien adapter geschaalde waarden levert; anders DisplayRole blijft adapter-DTO |
| **Views** | Geen wijziging verwacht (adapter-first) |

### Schaal-algoritme (voorstel)

Voor elke MC-rij met lifecycle-banden `(p10, p50, p90)` en synthetisch `FMResult`:

```
display_p50 = scalar_metric(project, fmr, presentation, nb_filter)
scale = display_p50 / fmr.lifecycle_total_metric   # guard divide-by-zero
display_p10 = p10 * scale
display_p90 = p90 * scale
```

Alternatief (preferred als buckets betrouwbaar zijn): bereken P10/P50/P90 **direct**
via bucket-series per metric (analytisch patroon uit
`contribution_horizon_value_service`) en schaal MC-banden proportioneel alleen als
fallback. PRD laat implementatiekeuze open; **acceptatie** is pariteit met
analytisch pad op fixture-niveau.

### Compare-slot snapshot

Horizon komt uit **live** `WorkspaceStateSnapshot.contribution_presentation`,
niet uit bevroren slot-metadata — analist mag horizon wisselen tijdens compare;
beide kolommen herberekenen (zelfde gedrag als analytische FM compare vandaag).

---

## Testing Decisions

### Test seams

| Seam | Wat wordt bewezen |
|------|-------------------|
| **`apply_presentation_scale_to_mc_rows`** | lifecycle vs Ø per jaar vs specifiek jaar; NB-filter; tooltip band scaling |
| **`build_fm_detail_view` (MC)** | Geschaalde waarden bij `RunMode.MONTE_CARLO` |
| **`build_fm_detail_view_for_compare_slot` (MC)** | Compare MC slot pariteit met analytische slot onderzelfde `ContributionPresentation` |
| **Haarlem/regressie tracer** | FM001-klasse rij: MC vs analytisch binnen plausibele ratio (<10×) bij default horizon |

### Prior art

- `tests/test_slice80_fm_presentation_scale.py` — analytisch schaal-contract
- `tests/test_slice100_compare_mixed_fm.py` — FM compare orchestrator
- `tests/test_slice100_mc_p50_rollups.py` — synthetische `FMResult` + `horizon_profile`
- `tests/test_desktop_contribution_horizon_value_service.py` — scalar SSOT

### Regressie-gates

- Slice 98: MC band-formaat, seed, cancel ongewijzigd.
- Slice 100: Top 10/LCC compare, scenario workflow ongewijzigd.
- Lifecycle-horizon: MC FM-waarden ≈ pre-slice-101 (geen regressie op totals).
- Analytisch FM-pad: geen wijziging.

---

## Out of Scope

- **RF-semantiek** harmoniseren tussen MC en analytisch.
- **P10/P90 als aparte kolommen** in FM-tabel (blijft tooltip).
- **Mean i.p.v. P50** voor MC FM (productkeuze slice 100/ADR-0018 blijft P50).
- **Onafhankelijke stochastische kosten/downtime** (PR3/ADR-0018 fase 2).
- **Delta-tabel** (B − A per FM).
- **Persistente horizon per scenario-slot** (horizon blijft global workspace state).

---

## Issue breakdown (voor `to-issues`)

| # | Issue | Type | Samenvatting |
|---|-------|------|--------------|
| 01 | MC presentation-scale helper | AFK | Pure adapter-functie + unit tests (lifecycle / Ø / jaar / NB-filter) |
| 02 | Single-run MC FM pad | AFK | `build_fm_detail_view` MC branch gebruikt helper |
| 03 | Compare MC FM slot | AFK | `build_fm_detail_view_for_compare_slot` MC branch gebruikt helper |
| 04 | Mixed compare regressie | AFK | Tracer op Haarlem-achtige fixture: default horizon, ratio-plausibiliteit |
| 05 | HILT checklist | HITL | Handcheck FM compare default + lifecycle + horizon-switch |

**Geschatte volgorde:** 01 → 02 → 03 → 04 → 05.

---

## Acceptance criteria (slice-niveau)

- [ ] MC FM single-run kolommen volgen `ContributionPresentation` (default **Ø per jaar**).
- [ ] MC FM compare-slot volgt dezelfde presentation als analytische compare-slot.
- [ ] MC band-tooltips (P10/P90) consistent met geschaalde kolom-P50.
- [ ] Horizon **Levensduur**: MC FM-waarden ≈ lifecycle P50 (geen regressie t.o.v. vóór fix).
- [ ] Haarlem demo mixed compare: geen schijnbare ~60× FM-verschillen bij default horizon.
- [ ] Geen wijziging aan Top 10/LCC/compare aggregate paden.
- [ ] Adapter unit tests groen; HILT101 handcheck gedocumenteerd.

---

## Further Notes

- **Relatie HILT100:** aggregate LCC/NB-jaarcurves zijn gefixt via `horizon_profile`
  op MC P50-rollups; deze slice sluit de **FM-tabel-presentatie-gap** — complementair,
  geen duplicaat.
- **Relatie slice 80:** analytisch FM schaal-contract is de SSOT; MC koppelt daarop
  via synthetische `FMResult`, niet via parallelle formules.
- **Product-uitleg analist:** P50 blijft mediaan onder onzekerheid; na deze slice
  is FM vergelijkbaar **op dezelfde tijdshorizon** — uitleg discrete banden (P10=0,
  P50=2) blijft relevant maar niet verergerd door horizon-mismatch.
- **ADR-amendement (licht):** ADR-0018 §Presentatie kan één zin toevoegen: FM MC
  kolommen respecteren `ContributionPresentation` (slice 101). Optioneel in issue 01.

---

## Akkoord

| Rol | Naam | Datum | GO / NO-GO | Opmerkingen |
|-----|------|-------|------------|-------------|
| Product/analist | | | | |
| Agent/implementatie | | | | |
