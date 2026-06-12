# PRD — RCM2 desktop slice 66 (REV-segment survival: conditionele noemer per segment)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** AFK (motor + regressie + parity-gate)  
**Parent:** ADR-0008 (RCM-Cost parity); slice 65 (modelcontrole); slice 52 (`aw_mc_lifecycle_horizon`); slice 51 (aging-distributies + REV-segmenten)  
**Referentie-fixture:** `tests/fixtures/RCMCostdata export_Gaarkeuken.rcm.json` (135 FM's met AW-benchmark; `aw_mc_lifecycle_horizon=True`)  
**Bronanalyse:** Claude Code parity-onderzoek 2026-06-05 — latente bug in `_conditional_failures_with_rev_segments` blootgelegd door AW MC-horizon

## Problem Statement

Na activatie van **AW MC-horizon** (`aw_mc_lifecycle_horizon=True`) en een parity-run op het Gaarkeuken-project valt de **modelcontrole AW** (ADR-0008) massaal door: **128 van 135** faalwijzen met benchmark falen de gate, met **astronomische kostenafwijkingen** (factoren tot ×739.000 t.o.v. AW `TotalCost`).

De analist kan daardoor:

- Geen betrouwbare AW-parity meer aflezen voor geïmporteerde RCM-Cost-projecten met oude assets en REV-taken.
- Ten onrechte concluderen dat het verschil “inherent Monte Carlo vs analytisch” of “repair quality / horizon-semantiek” is, terwijl een **rekenfout in de REV-segmentatie** de cascade (faalmomenten → downtime → kosten) explodeert.
- `aw_mc_lifecycle_horizon` niet veilig inschakelen, ook al is die semantiek nodig om # falen en AW `TotalW` te aligneren.

**Geverifieerde root cause:** in `_conditional_failures_with_rev_segments` wordt de conditionele overlevingskans `survival = 1 − F(effective_age)` **één keer** aan het begin van het studievenster berekend en daarna als **noemer voor elk REV-segment** hergebruikt — ook nadat een REV-taak de effectieve leeftijd via `rejuvenate_age` terugzet naar een veel jongere waarde. Voor een oud asset (leeftijd ≫ MTTF) is die initiële survival extreem klein (~2·10⁻⁷). Na een REV-reset is de CDF-toename in het volgende segment relatief groot (~0,09). Het quotiënt 0,09 / 2·10⁻⁷ ≈ 450.000 leidt tot `expected_failures` in de honderdduizenden — exact teruggezien op FM `06H-350.2.12.2.1.A.1` (mttf=25 jr, σ=3,75, leeftijd=44 jr, REV elke 20 jr).

**Gedrag zonder REV** blijft normaal; **één REV-segment** (lifecycle=70) geeft plausibele ~2 faalmomenten; **tweede REV-segment** (lifecycle=90) explodeert naar ~450.603. De bug treft dus **oude assets met REV-schema** wanneer de studiehorizon **meerdere REV-cycli** omvat — precies het scenario dat AW MC-horizon vaker activeert.

## Solution

Corrigeer de REV-segmentatie zodat de conditionele noemer **per segment** wordt bepaald op de leeftijd **na** de voorgaande REV-rejuvenatie — consistent met de niet-REV-tak die lokaal `(f_end − f_at_start) / survival` berekent met `survival` op segmentstart.

Daarna:

1. Voeg een **gerichte regressietest** toe (oude asset + REV-interval + lange horizon) die exponentiële explosie afvangt.
2. Herhaal **parity-gate** op Gaarkeuken: verwacht dat het overgrote deel van de 128 fails verdwijnt (kosten/downtime volgen faalmomenten).
3. Bevestig dat **`aw_mc_lifecycle_horizon` default `False` blijft**; na fix is handmatig inschakelen veilig voor parity-werk, zonder de gate systematisch te breken.

Geen UI-wijziging nodig; dit is een **motor-correctheidsslice**.

## User Stories

### Analist — parity en vertrouwen

1. Als **analist**, wil ik dat RCM2 `expected_failures` voor oude assets met REV-taken **niet exponentieel explodeert** wanneer de studiehorizon meerdere REV-cycli omvat, zodat LCC- en parity-cijfers fysisch plausibel blijven.
2. Als **analist**, wil ik dat **modelcontrole AW** op Gaarkeuken (met `aw_mc_lifecycle_horizon=True`) na de fix **grotendeels groen** wordt, zodat ik AW-importen weer kan valideren.
3. Als **analist**, wil ik dat extreme `total_cost_eur`-afwijkingen (×10⁵+) **verdwijnen** voor de getroffen aging-FM's, zodat ik niet per FM hoeft te filteren op “obvious bugs”.
4. Als **analist**, wil ik **`aw_mc_lifecycle_horizon` kunnen inschakelen** zonder dat de motor onbruikbare resultaten produceert, zodat # falen beter aansluit bij AW `TotalW`-semantiek.
5. Als **analist**, wil ik dat **validatie-export** en **counterfactual # falen** na de fix consistente `ef_actual`-waarden tonen voor dezelfde FM's, zodat eerdere diagnostiek niet misleidend blijft.

### Maintainer — motor en SSOT

6. Als **maintainer**, wil ik dat `_conditional_failures_with_rev_segments` per segment **`survival` herberekent** op de actuele `age` aan segmentstart, zodat conditionele faalkans R(t|a) correct blijft na REV-rejuvenatie.
7. Als **maintainer**, wil ik dat de fix geldt voor **alle aging-distributies** in de REV-tak (`normal`, `truncated_normal_0`, `weibull_2p`), zodat slice 51-paden niet divergeren.
8. Als **maintainer**, wil ik dat de **niet-REV-tak** ongewijzigd blijft qua gedrag, zodat bestaande baselines zonder REV niet regresseren.
9. Als **maintainer**, wil ik dat **`expected_aging_lifecycle_faalmomenten_ssot`** en **`expected_failures_lifecycle`** de gecorrigeerde segmentlogica gebruiken, zodat FM-resultaten, LCC-horizon en parity-diagnostiek één SSOT delen.
10. Als **maintainer**, wil ik **`CACHE_INPUTS_VERSION` bumpen** na motorwijziging, zodat incrementele cache geen verouderde FM-hashes hergebruikt.
11. Als **maintainer**, wil ik dat **Monte Carlo aging-pad** (`test_aging_monte_carlo`) dezelfde `_conditional_failures_with_rev_segments`-functie blijft aanroepen, zodat analytisch en MC niet uit elkaar lopen door een tweede implementatie.

### Tester — regressie en parity

12. Als **maintainer**, wil ik een **unit-test** met expliciete getallen (leeftijd=44, mttf=25, σ=3,75, REV elke 20 jr) die afdwingt dat `expected_failures` bij lifecycle=70 plausibel (~2) blijft en bij lifecycle=90 **niet** naar ~450.000 springt, zodat de bug niet terugkomt.
13. Als **maintainer**, wil ik een **bovengrens-assertie** (bijv. `expected_failures < lifecycle_years / mttf × kleine_factor`) voor het explosie-scenario, zodat regressie robuust is zonder exacte AW-match te vereisen.
14. Als **maintainer**, wil ik een **Gaarkeuken parity-regressietest** die `build_parity_report` draait met `aw_mc_lifecycle_horizon=True` en een **drempel op fail-count** (bijv. ≪ 128 fails) asserteert, zodat ADR-0008-gate de fix end-to-end bewaakt.
15. Als **maintainer**, wil ik dat bestaande **`test_rcm_cost_benchmark`**- en **`test_failure_parity_validation`**-tests groen blijven of bewust worden bijgewerkt met nieuwe verwachtingen, zodat geen stille drift ontstaat.
16. Als **maintainer**, wil ik dat **Haarlem-demo** en andere fixtures **zonder oude+REV+meervoudige cycli** ongewijzigde uitkomsten houden (of alleen binnen bestaande tolerantie), zodat brede regressie beperkt blijft.

### Product / release

17. Als **product owner**, wil ik dat **`aw_mc_lifecycle_horizon` niet `True` als default** wordt voordat deze slice is afgerond, zodat nieuwe gebruikers geen systematisch falende parity-gate zien.
18. Als **trainer**, wil ik in documentatie/note kort vermelden dat AW MC-horizon **meerdere REV-cycli** activeert en daardoor deze bug zichtbaar maakte, zodat analisten de causaliteit begrijpen.

### Scope-afbakening (bewust niet in deze slice)

19. Als **analist**, accepteer ik dat **residuele parity-afwijkingen** (Monte Carlo vs analytisch, repair quality-import, CM-overlay) **na deze fix** kunnen blijven bestaan, zodat slice 66 zich op de rekenfout concentreert en niet het volledige parity-programma opnieuw opent.

## Implementation Decisions

### Kernfix — REV-segment conditionering

- **Module:** `rcm_core/distributions.py`, functie `_conditional_failures_with_rev_segments`.
- **Huidig gedrag (fout):** `survival` wordt éénmalig berekend op `effective_age` bij `clock_start`; elk segment gebruikt `(f_hi − f_lo) / survival` met die vaste noemer; `age` wordt wel bijgewerkt na REV, `survival` niet.
- **Gewenst gedrag:** voor elk segment `[b0, b1]`:
  - Bepaal `age` aan segmentstart (na eerdere REV-rejuvenaties).
  - Herbereken `survival_seg = 1 − F(age)` (distributie-afhankelijk, zelfde takken als `f_lo`).
  - Als `survival_seg < ε`: segmentdraagt 0 bij (consistent met vroege return bij globale survival).
  - Anders: `total += (f_hi − f_lo) / survival_seg`.
  - Pas REV-rejuvenatie toe aan segmenteinde zoals nu.
- **Consistentie:** aligneer met niet-REV-tak (regels 273–281) waar noemer en teller op hetzelfde interval worden bepaald.

### Horizon en config (geen semantiek-wijziging)

- **`aw_mc_lifecycle_horizon`** en `effective_lifecycle_end_age` / `study_duration_years` blijven ongewijzigd; slice 66 **fixt de motor**, niet de horizon-definitie.
- **Default** `aw_mc_lifecycle_horizon=False` blijft; geen automatische migratie van bestaande projecten.

### Cache en run

- **`CACHE_INPUTS_VERSION`** in `rcm_core/cache.py` verhogen — FM-resultaten wijzigen voor getroffen invoer.
- Geen wijziging aan domain model, editing schema, of import-contract.

### Parity en diagnostiek

- **`build_parity_report`** (`rcm_core/rcm_cost_benchmark.py`) blijft ongewijzigd; verbetering komt uit gecorrigeerde `FMResult`-inputs.
- **Validatie-export** (`failure_parity_validation`) profiteert automatisch; geen exportformaat-wijziging.

### Issues-splitsing (implementatievolgorde)

| Issue | Inhoud |
|-------|--------|
| **01** | Kernfix + unit/regressietest op `_conditional_failures_with_rev_segments` + `CACHE_INPUTS_VERSION` |
| **02** | Gaarkeuken parity-gate regressie (`build_parity_report` fail-count drempel) |
| **03** | Documentatie-note in slice-KANBAN / ADR-0008-referentie: causaliteit bug ↔ AW MC-horizon; geen default flip |

## Testing Decisions

### Wat maakt een goede test

- Test **extern gedrag** (faalmomenten, parity-verdicts), niet interne loop-indexen of private variabelen.
- Gebruik **deterministische invoer** (vaste MTTF, σ, leeftijd, REV-interval) met **expliciete verwachtingen** uit de root-cause-analyse.
- Prefereer **bestaande seams** boven nieuwe; alleen nieuwe tests waar geen dekking is.

### Test-seams (hoog → laag) — ter bevestiging vóór implementatie

| Prioriteit | Seam | Wat wordt geasserteerd |
|------------|------|-------------------------|
| **1 (primair)** | `_conditional_failures_with_rev_segments(...)` direct | lifecycle=70 ≈ 2; lifecycle=90 ≪ 450.000; zonder REV monotone groei |
| **2** | `expected_failures_lifecycle` / SSOT-keten | Zelfde FM-invoer via publieke API geeft niet-geëxplodeerde waarden |
| **3** | `build_parity_report(project, fm_results)` op Gaarkeuken-fixture | `fail_count` daalt sterk vs baseline 128 (exacte drempel in issue 02) |
| **4 (secundair)** | `build_failure_validation_report` | `ef_actual` voor top-fail FM's binnen plausibel bereik |

**Geen** Qt-adaptertests nodig; **geen** nieuwe CLI-seam.

### Prior art

- `tests/test_aging_monte_carlo.py` — roept `_conditional_failures_with_rev_segments` aan; uitbreiden of aanvullende testmodule `test_rev_segment_survival.py`.
- `tests/test_rcm_cost_benchmark.py` — `build_parity_report` pass/fail-patronen.
- `tests/test_failure_parity_validation.py` / `tests/test_failure_validation_export.py` — Gaarkeuken-fixture skipif-patroon.
- `tests/test_lifecycle_horizon.py` — horizon-semantiek blijft apart getest; niet mengen met segmentfix.

### Acceptatie-drempels (voorstel)

- Unit: `expected_failures(lifecycle=90) < 50` (ruim onder 450.603; exacte bound in issue).
- Parity: `fail_count ≤ 20` op Gaarkeuken (ruim onder 128; finetune na eerste groene run — in issue vastleggen).

## Out of Scope

- **Repair quality-import** uit AW Excel (B1-counterfactual) — apart traject; niet blocker voor deze motorfix.
- **Monte Carlo vs analytisch** inherent verschil — blijft residuele parity na fix.
- **CM-overlay / disabled PM-taken** — scenario-semantiek ongewijzigd.
- **UI voor modelinstellingen** — geen wijziging aan `aw_mc_lifecycle_horizon`-checkbox; alleen gedrag na fix.
- **Weibull/truncated-normal MC-parity** uitbreiding — alleen als bestaande tests breken.
- **Portfolio-merge parity** (slice 64) — geen projecttotaal-gate in deze slice.
- **Automatisch `aw_mc_lifecycle_horizon=True` zetten** bij AW-import — expliciet niet; analist kiest bewust na fix.

## Further Notes

### Causaliteitsketen (analyse-samenvatting)

```
aw_mc_lifecycle_horizon=True
  → studiehorizon = current_age + lifecycle_years (langere kalender)
  → oude asset doorloopt meerdere REV-cycli
  → stale survival-noemer in REV-segmenten
  → expected_failures ×10⁵–10⁶
  → total_cost_eur / downtime explodeert
  → ADR-0008 parity-gate: 128/135 fail
```

### Referentie-FM (regressie-anker)

| Veld | Waarde |
|------|--------|
| FM | `06H-350.2.12.2.1.A.1` |
| failure_type | aging (normaal) |
| mttf_jaar | 25 |
| sigma | 3,75 |
| current_age | 44 |
| REV | interval 20 jr, aging_effect 100% |
| lifecycle=70 | expected_failures ≈ 2,06 (OK) |
| lifecycle=90 | expected_failures ≈ 450.603 (BUG) |

### Relatie tot eerdere parity-werk

- Slice 65 leverde **modelcontrole AW**; slice 66 maakt die gate **betrouwbaar** onder AW MC-horizon.
- Validatie-export (counterfactual # falen) blijft diagnostisch; na fix verschuift dominantie van “horizon/residu” naar echte restverschillen (MC, import, scenario).

### Risico's

- **Te strakke parity-drempel** in regressietest kan flaky zijn als AW-band breed is — begin met fail-count, niet per-FM exacte €-match.
- **Andere latente REV-edge cases** (gelijktijdige REV's, interval=0) blijven buiten scope tenzij tests falen.
