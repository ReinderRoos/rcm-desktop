# PRD — RCM2 desktop slice 71 (NB-effectfilter & workspace UX vereenvoudiging)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** Presentatielaag + UX-vereenvoudiging + kosten-diagnose  
**Parent:** slice **70** (**done** — effectimpact deep module, motor split, hybride Top 10); slice **68** (CM-overlay run alignment); slice **33** (Top 10 metrics); `/improve-codebase-architecture` review (2026-06-05)  
**Referentie-fixtures:** `tests/fixtures/RCMCostdata export_CM.xlsx`; Gaarkeuken `.rcm.json`; golden cause `06H-350.1.1.1.1.1.A.1`  
**Analist-bevestiging (2026-06-05):** Slice 70 UX (bron Effectklasse + metric Effectimpact) loopt door elkaar met Niet-beschikbaarheid; te veel knoppen. Lifecycle-kosten lijken gestegen (~60 M → ~160 M) na recente wijzigingen — eerst diagnosticeren, daarna UX vereenvoudigen.

## Problem Statement

Na slice 70 kan de analist effectimpact per effectklasse zien, maar de **resultatenwerkruimte** is visueel en conceptueel verwarrend:

| Aspect | Huidig gedrag (slice 70) | Gewenst gedrag |
|--------|--------------------------|----------------|
| **Top 10 bron** | Drie knoppen: Component, Faalwijze, **Effectklasse** | Twee knoppen: Component, Faalwijze |
| **Metric dropdown** | Vier opties incl. **Effectimpact** | Drie opties: Niet-beschikbaarheid, Faalmomenten, Kosten |
| **NB per effect** | Alleen via bron Effectklasse + metric Effectimpact | **Vervolgfilter** bij metric Niet-beschikbaarheid (multi-select op beschikbaarheid-effecten) |
| **Tijdsplot** | EUR-curve (CM/PM); slice 70 issue 09 UI niet afgerond | Zelfde metric + NB-effectfilter als Top 10; plot wisselt per metric |
| **Lifecycle-kosten KPI** | ~160 M Euro na recente run | Verwacht ~60 M met CM-overlay (slice 68); regressie onderzoeken |

De analist wil **één mentaal model**: kies metric (NB / faalmomenten / kosten), en wanneer NB actief is, filter optioneel op niet-beschikbaarheids-effecten (Schutten, Keren, …). Die selectie geldt **overal** in de werkruimte (Top 10 op alle PBS-lagen, Tijdsplot op alle PBS-lagen).

## Solution

Voer een **UX-vereenvoudigingsslice** uit die slice 70's hybride Top 10-model vervangt door een gedeeld **NB-effectfilter**, en los parallel een **kosten-regressie-diagnose** op:

1. **Issue 00** — Tracer bullet: CM-overlay vs zonder overlay; documenteer verwachte kostenband; slice 68-regressie herbevestigen.
2. **Verdiep `EffectImpactService`** — enige seam voor NB-scalars en NB-jaarreeksen met optionele `klasse_ids`-filter; geen tweede pad via bron Effectklasse.
3. **`EffectNbFilterSet` in workspace state** — multi-select op effectklassen met categorie beschikbaarheid; leeg = totale NB (slice 33, incl. verborgen NB).
4. **Verwijder** `SOURCE_EFFECTKLASSE`, `METRIC_EFFECTIMPACT`, hybride `set_source`-logica.
5. **Top 10** — metric dropdown 3-way; NB-effectfilter zichtbaar bij metric NB; ranking via gefilterde NB-scalar per FM → PBS/Faalwijze aggregatie.
6. **Tijdsplot** — gedeelde metric-combobox + NB-effectfilter; bij metric Kosten bestaand EUR-gedrag + PM-type-filters; bij metric NB jaarreeks uren/% via gefilterde effecten; bij Faalmomenten faalmomenten-reeks.
7. **Docs & regressie** — `CONTEXT.md` term **NB-effectfilter**; supersede slice 70 HITL UX-besluit; migreer slice 70 Top 10-tests.

Motor split (slice 70 issue 02), taxonomie (issue 11), inspector, functierapport effecttabel, validatie-export blijven **behouden**.

## User Stories

### Analist — vereenvoudigde werkruimte

1. Als **analist**, wil ik **geen aparte knop Effectklasse** in Top 10, zodat bron Component/Faalwijze overzichtelijk blijft.
2. Als **analist**, wil ik in de metric-dropdown **alleen** Niet-beschikbaarheid, Faalmomenten en Kosten, zodat Effectimpact niet naast NB staat.
3. Als **analist**, wil ik wanneer **Niet-beschikbaarheid** geselecteerd is een **vervolgdropdown** met multi-select op alle beschikbaarheid-effecten, zodat ik NB per Schutten/Keren/etc. kan filteren zonder van bron te wisselen.
4. Als **analist**, wil ik bij **lege effectselectie** de **totale NB** zien (CM + PM + verborgen NB), zodat mijn bestaande slice-33 workflow intact blijft.
5. Als **analist**, wil ik bij **één of meer geselecteerde effecten** de **som NB per geselecteerde effectklassen** zien, zodat ik gericht kan pareto-analyseren.
6. Als **analist**, wil ik het NB-effectfilter op **alle PBS-lagen** (hele project tot diepste component), zodat scope-navigatie consistent filtert.
7. Als **analist**, wil ik het **zelfde NB-effectfilter** in **Tijdsplot** als in Top 10, zodat ik niet opnieuw hoef te kiezen bij moduswissel.
8. Als **analist**, wil ik in Tijdsplot bij metric **Kosten** het bestaande EUR-curve-gedrag (CM/PM + type-filters REV/IN/…), zodat onderhoudsanalyse niet verandert.
9. Als **analist**, wil ik in Tijdsplot bij metric **Niet-beschikbaarheid** een **NB-jaarcurve** (uren of %), zodat effectontwikkeling over tijd zichtbaar is.
10. Als **analist**, wil ik in Tijdsplot bij metric **Faalmomenten** een faalmomenten-jaarcurve, zodat faalfrequentie over tijd zichtbaar is.
11. Als **analist**, wil ik horizon-keuzes (lifecycle / per jaar / kalenderjaar) en uren/% voor NB **behouden** in Top 10, zodat slice 33 consistent blijft.
12. Als **analist**, wil ik **RF en eenheid** in Top 10-tabel/tooltip bij gefilterde NB, zodat interpretatie auditbaar blijft.
13. Als **analist**, wil ik voor golden cause `06H-350.1.1.1.1.1.A.1` bij filter op Schutten-effecten **alleen beschikbaarheid-NB** zien (niet VGM-incidenten), zodat categorie-scheiding klopt.
14. Als **analist**, wil ik **compare A/B** dezelfde metric + NB-effectfilter respecteren, zodat scenariovergelijking effectbewust blijft.
15. Als **analist**, wil ik dat **veiligheidseffecten (VGM)** niet in het NB-effectfilter staan, zodat ik geen incidenten per ongeluk als downtime filter.
16. Als **analist**, wil ik na fresh run op Gaarkeuken **lifecycle-kosten ~60 M Euro** (CM-overlay), zodat de KPI vertrouwd blijft t.o.v. AW CM-scenario.
17. Als **analist**, wil ik begrijpen **waarom kosten anders zijn** wanneer CM-overlay uit staat (~160 M), zodat ik geen softwarebug verwar met analistische keuze.
18. Als **analist**, wil ik in **FM-inspector** effectrijen **ongewijzigd** bruikbaar houden, zodat detailverificatie slice 70 blijft werken.
19. Als **analist**, wil ik in **functierapport** effectimpact-tabellen **behouden**, zodat rapportage slice 70 niet terugvalt.
20. Als **analist**, wil ik dat **KPI-totalen** (lifecycle kosten, NB %) **niet** afhangen van NB-effectfilter, zodat filters alleen ranking/plot beïnvloeden.

### Maintainer — architectuur

21. Als **maintainer**, wil ik **`EffectImpactService`** uitbreiden als **enige NB-presentatieseam** met filter, zodat Top 10 en Tijdsplot niet dupliceren.
22. Als **maintainer**, wil ik **`EffectNbFilterSet`** in `WorkspaceStateSnapshot`, analoog aan `LCCTypeFilterSet`, zodat cross-modus state één plek heeft.
23. Als **maintainer**, wil ik **`SOURCE_EFFECTKLASSE` en `METRIC_EFFECTIMPACT` verwijderen**, zodat de interface kleiner wordt dan de implementatie (deletion test).
24. Als **maintainer**, wil ik **presentatie-cache keys** het NB-effectfilter bevatten, zodat stale Top 10 na filterwissel voorkomen wordt.
25. Als **maintainer**, wil ik **`ResultsWorkspaceOrchestrator`** toolbar-plannen uitbreiden voor filter-zichtbaarheid in Top 10 én Tijdsplot, zodat bind-only venster dun blijft.
26. Als **maintainer**, wil ik **geen Qt in kern deep modules**, zodat TDD op service-niveau blijft.
27. Als **maintainer**, wil ik **`CONTEXT.md`** term **NB-effectfilter** vastleggen en slice 70 hybride UX superseden, zodat toekomstige agents niet opnieuw bron Effectklasse voorstellen.
28. Als **maintainer**, wil ik **`CACHE_INPUTS_VERSION` niet bumpen** tenzij serialisatie wijzigt, zodat slice 71 puur presentatie is.
29. Als **maintainer**, wil ik **slice 70 motor split en taxonomie ongewijzigd** laten, zodat alleen presentatie/state wijzigt.
30. Als **maintainer**, wil ik **issue 00 groen** vóór UX-issues, zodat kosten en UX niet tegelijk debuggen.

### Tester — seams en regressie

31. Als **maintainer**, wil ik **integration tests** op `EffectImpactService.nb_scalar_for_fm` en `nb_yearly_series`, zodat gedrag overleefd refactors.
32. Als **maintainer**, wil ik **golden cause tests** voor gefilterde Top 10 ranking, zodat Schutten-filter nooit regresseren.
33. Als **maintainer**, wil ik **bucket-reconciliatie** voor NB-jaarreeks (som ≈ lifecycle scalar), zodat Tijdsplot betrouwbaar is.
34. Als **maintainer**, wil ik **`test_slice68_parity_run_alignment`** groen houden, zodat CM-overlay alignment bewaakt blijft.
35. Als **maintainer**, wil ik **bestaande slice 70 regressietests migreren** (hybride Top 10 → NB-filter model), zodat geen dubbele specs blijven.
36. Als **maintainer**, wil ik **pytest-qt smoke** voor NB-effectfilter zichtbaarheid (Top 10 + Tijdsplot), zodat UI-bindings gedekt zijn.
37. Als **maintainer**, wil ik **functierapport smoke** zonder workspace `SOURCE_EFFECTKLASSE`, zodat rapportage los van verwijderde UI blijft.

## Implementation Decisions

### Prioritering (9 issues)

| Issue | Focus | Type |
|-------|--------|------|
| **00** | Lifecycle-kosten regressie CM-overlay | AFK (blocker) |
| **01** | `EffectNbFilterSet` + NB-seam in `EffectImpactService` | AFK |
| **02** | Gefilterde Top 10 aggregatie (scalar per FM) | AFK |
| **03** | Workspace state: filter + verwijder hybrid Effectklasse/Effectimpact | AFK |
| **04** | Top 10 UI: metric 3-way + multi-select NB-effectfilter | AFK |
| **05** | NB-jaarreeks + Tijdsplot dataseam | AFK |
| **06** | Tijdsplot UI: gedeelde metric + NB-curve | AFK |
| **07** | Regressie, CONTEXT.md, slice 70 test-migratie | AFK |
| **08** | Functierapport smoke (effecttabel zonder workspace bron Effectklasse) | AFK |

**Aanbevolen volgorde:** 00 → 01 → 02 → 03 → 04 → (05 ∥ na 03) → 06 → 07 → 08.

### Test seams (hoogste seam eerst)

1. **`EffectImpactService` (kern, Qt-vrij)** — publieke API:
   - `list_nb_effect_klassen(project)` → opties voor UI (alleen categorie beschikbaarheid)
   - `nb_scalar_for_fm(project, fmr, *, klasse_ids, presentation)` → één getal per FM
   - `nb_yearly_series(project, fm_results, *, klasse_ids, scope_id, fm_ids)` → horizon buckets
   - `klasse_ids=None` of lege `EffectNbFilterSet` → totale NB (slice 33 semantiek)
2. **`build_contribution_rows`** — integratie: PBS/Faalwijze ranking met `effect_nb_filter` uit snapshot
3. **`WorkspaceStateSnapshot` + orchestrator plans** — zichtbaarheid filter; geen Effectklasse/Effectimpact constanten
4. **LCC/Tijdsplot builder** — metric-gedreven curve (EUR vs NB vs faalmomenten); NB-filter gedeeld met Top 10
5. **pytest-qt smoke** — laagste seam; alleen zichtbaarheid/enabling widgets

Geen nieuwe parallelle “EffectFilterService” — uitbreiding van bestaande deep module (deletion test: complexiteit verdwijnt niet als module weg is).

### Issue 00 — Kosten-diagnose

- Tracer op Gaarkeuken-fixture: `total_cost_eur` met `materialize_cm_overlay_project` binnen bekende band (~60 M).
- Tegen-run documenteren zonder overlay (~160 M) — analistische verwachting, geen bug.
- Herbevestig slice 68: median `|ef_actual − ef_cm_overlay| < 0.01`, 0× C1 validatie-actie.
- Als overlay actief maar kosten toch ~160 M → apart bug-issue (buiten slice 71 scope).

### Issue 01 — NB-effectfilter datamodel

```python
@dataclass(frozen=True)
class EffectNbFilterSet:
    selected_klasse_ids: frozenset[str] = frozenset()

    def is_all(self) -> bool:
        return len(self.selected_klasse_ids) == 0
```

- Leeg = alle NB (totaal downtime pad, niet som enkel effectlinks).
- Gevuld = som gepresenteerde NB per geselecteerde klassen via categorie-formules (alleen beschikbaarheid).
- UI-labels uit `EffectKlasse.omschrijving`; invalid IDs genegeerd of validatie in state-setter.

### Issue 02 — Top 10 aggregatie

- Bij metric NB: roep `nb_scalar_for_fm` i.p.v. `contribution_horizon_value_service._unavailability_scalar` wanneer filter actief; bij lege filter delegatie naar bestaand totaal-NB pad.
- Bij metric Faalmomenten/Kosten: ongewijzigd; effectfilter verborgen.
- Verwijder tak `source == SOURCE_EFFECTKLASSE or metric == METRIC_EFFECTIMPACT` → vervangen door metric NB + filter.

### Issue 03 — Workspace state

- Snapshot-veld: `effect_nb_filter: EffectNbFilterSet`.
- Verwijder: `SOURCE_EFFECTKLASSE`, `METRIC_EFFECTIMPACT`, hybride `set_source`, `ALL_SOURCES` derde entry.
- Migratie: opgeslagen sessions met legacy source/metric → normalize naar PBS + NB + lege filter.
- Cache key string: voeg serialisatie filter toe.

### Issue 04 — Top 10 UI

- Verwijder Effectklasse-knop uit sub-balk.
- Metric-combobox: drie items.
- Multi-select widget (checkable combo of list) voor NB-effecten; alleen zichtbaar als orchestrator plan `effect_nb_filter_visible`.
- Horizontale controls ongewijzigd voor horizon/uren/%.

### Issue 05 — Tijdsplot dataseam

- Uitbreid LCC-view builder: bij metric Kosten → bestaande `LCCPlanningCurve` EUR.
- Bij metric NB → NB-jaarreeks uit `nb_yearly_series` + `ContributionPresentation`-equivalent (uren/%).
- Bij metric Faalmomenten → bestaande bucket faalmomenten-logica.
- Reconciliatie: som buckets ≈ lifecycle scalar (tolerantie zoals slice 70 issue 09).

### Issue 06 — Tijdsplot UI

- Metric-combobox + NB-effectfilter **gedeeld** met Top 10 (zelfde workspace state, niet dubbele widgets met divergerende state).
- PM-type-filterbalk (`LCCTypeFilterSet`) alleen zichtbaar bij metric Kosten.
- Chart/tabel labels eenheid-aware (uren, %, EUR, faalmomenten).

### Issue 07 — Docs & regressie

- `CONTEXT.md`: sectie **NB-effectfilter**; pas Effectimpact-sectie aan (geen bron Effectklasse meer in Top 10).
- Note in spike of ADR-addendum: supersede slice 70 HITL besluit #5 (hybride UX).
- Migreer `test_slice70_top10_effectklasse.py` → `test_slice71_nb_effectfilter.py`.
- KANBAN_HANDOFF.md in slice-map.

### Issue 08 — Rapportage

- Functierapport effectimpact-tabel blijft via `EffectImpactService.aggregate` + functie-scope FM-ids.
- Geen afhankelijkheid van verwijderde workspace constanten.
- Smoke test: PDF-sectie bevat effectrijen voor testfunctie.

## Testing Decisions

**Goede tests** beschrijven **extern gedrag** via publieke seams:

- “Lege filter + metric NB + scope root → zelfde ranking als slice 33 baseline”
- “Filter op één Schutten-klasse → ranking som = aggregate NB voor die klasse”
- “NB jaarreeks som ≈ scalar binnen tolerantie”
- “Metric Kosten Tijdsplot → PM-type-filters werken; NB-filter verborgen”

**Modules onder test:** `EffectImpactService`, `contribution_chart_service`, `results_workspace_state`, orchestrator plans, LCC/NB series builder, functierapport materialization.

**Prior art:** `test_slice70_effect_impact_service.py`, `test_slice70_top10_effectklasse.py`, `test_slice68_parity_run_alignment.py`, `test_slice33_*`, `test_effect_per_jaar.py`, golden cause in `test_slice70_regression.py`.

**pytest-qt:** alleen smoke zichtbaarheid multi-select en metric sync Top 10 ↔ Tijdsplot.

## Out of Scope

- Wijziging slice 70 motor split, taxonomie-import, FM-inspector DTOs, validatie-export effecttab, EffectCost-pariteit.
- Monte Carlo / AW volledige effect-pariteit.
- NB-effectfilter op veiligheid/kosten/overig categorieën (alleen beschikbaarheid).
- KPI-totalen filteren op effect (filter geldt ranking/plot only).
- Bidirectionele AW-export.
- Modelcontrole-dialog tab Effecten (slice 70 backlog).

## Further Notes

### Supersede slice 70 UX

Slice 70 HITL besluit #5 (hybride: bron Effectklasse → metric Effectimpact) wordt **vervangen** door NB-effectfilter bij metric Niet-beschikbaarheid. Deep module `EffectImpactService` en motor split **blijven**.

### Architectuur (improve-codebase-architecture)

**Top recommendation:** verdiep `EffectImpactService`; verwijder ondiepe bron/metric-hybride. Localiteit voor NB-formules + filter; leverage voor alle consumenten via `{ metric, effect_nb_filter, presentation }`.

### Start implementatie

```
/tdd slice 71 issue 00
```

Daarna: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08.
