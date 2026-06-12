# Slice 33 — Werkruimte: Top 10-sub-balk, modi opruimen, metrics zonder Risico

**Triage:** done  
**Type:** AFK (adapter + werkruimte-UI; geen `rcm_core`-schema-wijziging)  
**Parent:** slice 23 (resultatenwerkruimte), slice 32 (labels/KPI/faalwijze-label), grill-me prio 4–6 (2026-05-19)  
**Supersedes (gedeelte):** slice 23 modi *Niet-beschikbaarheid* / *Preventief onderhoud*; slice 31 (PM-modus what-if-alignment — modus verdwijnt); metric *Risico* in Top 10  
**Versie:** 1.0  
**Datum:** 2026-05-19

## Problem Statement

Na slice 32 blijven in de resultatenwerkruimte drie UX- en modelproblemen:

1. **Modus-rommel:** Knoppen *Niet-beschikbaarheid* en *Preventief onderhoud* overlappen met **Tijdsplot** (LCC) en **Top 10**; PM-modus was tijdelijk uitgelijnd met LCC (slice 31) maar voegt voor analisten weinig toe na what-if in Tijdsplot.
2. **Zwakke Top 10-context:** Bron-toggles (Component / Faalwijze) en de metric-combobox staan op één rij met alle modi; buiten Top 10 zijn ze uitgeschakeld maar nog zichtbaar — de koppeling met Top 10 is onduidelijk.
3. **Risico als metric:** *Risico* (`expected_failures × p_ongewenste_gebeurtenis`) is een aggregaat dat weinig inzicht geeft; analisten willen **faalmomenten** en **niet-beschikbaarheid** expliciet, desnoods **per jaar** of over de **LCC-periode**, en NB als **uren** of **percentage** (8760 u/jaar, 24/7). Een aparte metric *Downtime* overlapt met NB in uren.

Daarnaast moet *Risico* ook uit de **scenariovergelijking** (CM/PM) verdwijnen als presentatie-KPI, zonder de motor te breken.

## Solution

1. **Modi terugbrengen tot drie:** **Top 10** | **Tijdsplot** | **FM-detail** — volledige verwijdering van NB- en PM-modus (UI, state, pagina’s, render-pad, workspace-koppelingen).
2. **Top 10-sub-balk:** Label *Top 10:* met Component | Faalwijze | metric-combobox; alleen zichtbaar in Top 10-modus.
3. **Metrics Top 10:** **Faalmomenten**, **Niet-beschikbaarheid**, **Kosten** — geen *Risico*, geen aparte *Downtime*.
4. **Horizon- en weergave-toggles** (alleen bij Faalmomenten of Niet-beschikbaarheid):
   - **Per LCC-periode** | **Per jaar**; bij per jaar een combobox: *Ø per jaar* (default) | kalenderjaren uit de horizon.
   - Bij **Niet-beschikbaarheid** extra: **Uren** (default) | **%**; bij per jaar default = gemiddelde uren/jaar uit LCC-buckets, optioneel één kalenderjaar.
5. **Waarde-SSOT:** Per-jaar NB en faalmomenten via dezelfde bucket-logica als LCC/NB-proxy (`horizon_profile`, `lcc_profile`-patroon); lifecycle-totalen reconciliëren met motor-`FMResult`; gemiddelde per jaar = som bucket-waarden / aantal horizonjaren.
6. **Risico uit UI:** Top 10 + scenariovergelijking + betreffende tooltips; `risk_contribution` blijft in `FMResult` / cache (backwards compat).

## User Stories

### Modi opruimen (prio 5)

1. Als analist wil ik alleen **Top 10**, **Tijdsplot** en **FM-detail** als modi, zodat ik niet tussen dubbele tijdreeks-views hoef te wisselen.
2. Als analist wil ik **niet-beschikbaarheid over tijd** via Tijdsplot en Top 10 (metric), zodat de aparte NB-modus overbodig is.
3. Als analist wil ik **preventief/PM over tijd** via Tijdsplot (filters, jaardetail, what-if), zodat de aparte Preventief-modus overbodig is.
4. Als trainer wil ik dat na verwijdering van PM-modus de **what-if-hint** van slice 31 niet meer als losse modus verschijnt, zodat uitleg in Tijdsplot-status/tooltip kan.
5. Als ontwikkelaar wil ik **geen dode pagina’s** (`unavailability_page`, `pm_page`) of render-paden meer, zodat onderhoud daalt.
6. Als ontwikkelaar wil ik bij **migratie** van opgeslagen workspace-state `preventief_onderhoud` → `lcc` en `niet_beschikbaarheid` → `bijdragen`, zodat oude sessies niet crashen.
7. Als tester wil ik dat bestaande **Tijdsplot- en Top 10-tests** groen blijven na modus-verwijdering.

### Top 10-sub-balk (prio 4)

8. Als analist wil ik een duidelijke **Top 10:-balk** met bron en metric, zodat ik zie dat deze keuzes bij Top 10 horen.
9. Als analist wil ik in **Tijdsplot** of **FM-detail** géén bron/metric-controls van Top 10 zien, zodat de toolbar rustig blijft.
10. Als analist wil ik dat Component/Faalwijze **sticky** blijven bij moduswissel terug naar Top 10, zodat mijn ranking-voorkeur behouden blijft.
11. Als gebruiker met klein venster wil ik dat de sub-balk **niet de modus-knoppen verdringt**, zodat moduswissel bereikbaar blijft.

### Metrics zonder Risico (prio 6 — basis)

12. Als analist wil ik **geen Risico-metric** meer in Top 10, zodat ik niet het aggregaat `p(OG) × faalmomenten` rank.
13. Als analist wil ik **geen aparte Downtime-metric**; downtime zie ik via **Niet-beschikbaarheid → Uren**, zodat één duidelijk pad bestaat.
14. Als analist wil ik in Top 10 **Faalmomenten**, **Niet-beschikbaarheid** en **Kosten** kunnen kiezen, zodat frequentie, impact en geld gedekt zijn.
15. Als analist wil ik dat **Kosten** geen horizon-toggles krijgt (lifecycle-totaal `total_cost_eur` per FM), zodat de sub-balk simpel blijft bij Kosten.
16. Als productowner wil ik **Risicobijdrage** uit de **CM/PM-scenariovergelijking** halen, zodat de UI geen risico-aggregaat meer promoot.
17. Als trainer wil ik tooltips van scenariovergelijking **zonder “risico”** als KPI-label, zodat copy consistent is.

### Horizon per jaar / LCC-periode (Faalmomenten + NB)

18. Als analist wil ik **per LCC-periode** faalmomenten of NB% / uren zien (zoals nu lifecycle-totalen), zodat ik het hele project vergelijk.
19. Als analist wil ik **per jaar** standaard het **gemiddelde per jaar** zien (LCC-bucket-gemiddelde), zodat ik jaarlijkse grootteorde krijg zonder eerst een jaar te kiezen.
20. Als analist wil ik uit een **jaar-combobox** een **specifiek kalenderjaar** kiezen, zodat ik dat jaar in Top 10 kan ranken.
21. Als analist wil ik dat **faalmomenten per jaar** uit dezelfde bucket-verdeling komen als LCC-correctief/NB-proxy, zodat Top 10 en Tijdsplot niet tegenstrijdig zijn.
22. Als analist wil ik dat **NB per jaar in uren** de som `cor_downtime + hidden_nb + PM-downtime` per bucket is (zoals NB-proxy), zodat NMF-verborgen NB meetelt.
23. Als tester wil ik dat de **som over alle jaren** (per FM) reconcileert met lifecycle-totalen binnen tolerantie, zodat de proxy betrouwbaar blijft.
24. Als analist wil ik bij **Ø per jaar** in de tabelkop/tooltip zien dat het een **gemiddelde** is, zodat ik niet verwar met een enkel jaar.

### NB-weergave uren / percentage

25. Als analist wil ik NB als **uren downtime** zien (default bij per jaar: gemiddelde uren/jaar), zodat ik absolute impact zie.
26. Als analist wil ik NB als **percentage** zien (`uren / 8760 × 100` per jaar of over lifecycle), zodat ik 24/7-operationele tijd als basis heb.
27. Als analist wil ik de toggle **Uren | %** alleen bij metric **Niet-beschikbaarheid**, zodat Faalmomenten niet onnodig complex wordt.
28. Als analist wil ik bij **lifecycle + percentage** de bestaande definitie behouden (totale downtime / lifecycle-uren × 100), zodat gedrag herkenbaar blijft.

### Faalmomenten — symmetrie met NB

29. Als analist wil ik voor **Faalmomenten** dezelfde horizon-toggle en jaarkiezer als voor NB, zodat beide metrics hetzelfde tijdsvenster gebruiken.
30. Als analist wil ik **geen uren/%-toggle** bij Faalmomenten, zodat alleen NB de weergave-modus kiest.

### Presentatie en cache

31. Als ontwikkelaar wil ik **presentatie-cache** en workspace-render keys uitbreiden met horizon/jaar/weergave, zodat moduswissel geen verkeerde cache toont.
32. Als ontwikkelaar wil ik bij onbekende oude metric `risico` of `downtime` migreren naar veilige defaults, zodat tests en sessies stabiel blijven.

### Architectuur en kwaliteit

33. Als ontwikkelaar wil ik een **Qt-vrije** contribution-waarde-service, zodat pytest zonder QApplication de bucket-math dekt.
34. Als ontwikkelaar wil ik **views** alleen via `rcm_desktop.adapter` laten praten met run/LCC-data, zodat ADR UI/kern-decoupling geldt.
35. Als ontwikkelaar wil ik **geen `CACHE_INPUTS_VERSION`-bump**, zodat motor-output ongewijzigd blijft.
36. Als analist wil ik in **FM-detail** nog steeds lifecycle-kolommen (faalmomenten, downtime, kosten) zien zonder Risico-kolom, zodat detail consistent blijft met eerdere FM-tabel (geen Risico-kolom was al zo).

## Implementation Decisions

### Modus-model (vereenvoudigd)

```python
ALL_MODES = ("bijdragen", "lcc", "fm_detail")

# Migratie bij set_modus / snapshot-load:
#   "preventief_onderhoud" -> "lcc"
#   "niet_beschikbaarheid" -> "bijdragen"
```

- Verwijder `MODE_NIET_BESCHIKBAARHEID`, `MODE_PREVENTIEF_ONDERHOUD`, `pm_submode`, PM-subtoggle-UI, `unavailability_page`, `pm_page`, bijbehorende `_render_*` en chart-widgets in de werkruimte-view.
- **Behoud** adapter-modules `pm_chart_service` / `unavailability_chart_service` alleen zolang andere consumers (presentatie-cache, tests) ze nodig hebben; workspace-imports en render-paden weg. Presentatie-cache bijwerken zodat geen verwijzing naar verwijderde modi blijft.

### Top 10-presentatiestate (sticky)

```python
@dataclass(frozen=True)
class ContributionPresentation:
    horizon: Literal["lifecycle", "per_year"] = "per_year"
    year_choice: Literal["average"] | int = "average"  # int = kalenderjaar
    unavailability_display: Literal["hours", "percent"] = "hours"

# Alleen relevant als metric in ("faalmomenten", "niet_beschikbaarheid")
# en horizon == "per_year" -> year_combo zichtbaar
```

- Opnemen in `WorkspaceStateSnapshot` + setters op `ResultsWorkspaceState`.
- Metric-set: `ALL_METRICS = ("faalmomenten", "niet_beschikbaarheid", "kosten")`; verwijder `METRIC_RISICO`, `METRIC_DOWNTIME`.
- Migratie metric: `risico` → `niet_beschikbaarheid`; `downtime` → `niet_beschikbaarheid`.

### Deep module: contribution horizon values (nieuw)

**Verantwoordelijkheid:** Voor elke `FMResult` in scope een **scalar waarde** leveren voor aggregatie in Top 10, gegeven metric + `ContributionPresentation` + `RCMProject`.

| Ingang | Per LCC-periode | Per jaar (Ø) | Per jaar (kalenderjaar K) |
|--------|-----------------|--------------|---------------------------|
| Faalmomenten | `expected_failures` | mean(bucket faalmomenten) | bucket[K] faalmomenten |
| NB uren | CM+hidden+PM downtime totaal | mean(bucket uren) | bucket[K] uren |
| NB % | lifecycle % (bestaand) | uren_K/8760×100 of mean % | bucket[K] uren/8760×100 |
| Kosten | `total_cost_eur` | (n.v.t. — geen horizon-toggles) | |

- **Faalmomenten per bucket:** hergebruik patroon uit `lcc_profile` / motor `_faalmomenten_per_bucket` (random + aging SSOT); zelfde `ltap_horizon_bucket_count` als NB-proxy.
- **NB per bucket:** hergebruik logica uit bestaande NB-proxy-service (horizon_profile SSOT, legacy fallback + reconcile naar lifecycle downtime).
- **Geen dubbele reconcile in view:** service retourneert FM-niveau waarden; `contribution_chart_service` blijft aggregeren/ranken/top-N.

### Contribution chart service (bestaand, uitbreiden)

- `_value_extractor` vervangen door aanroep naar horizon-value-service.
- Verwijder risico/downtime-takken.
- Publieke API `build_contribution_rows` ongewijzigd qua parameters behalve dat callers `ContributionPresentation` via snapshot doorgeven (of service leest uit expliciete argumenten).

### Contribution table model

- Formatting: faalmomenten → int; kosten → €; NB uren → `h` met decimalen; NB % → `%` met 4 decimalen (pariteit huidige NB-metric).

### Results workspace view

- **Modus-rij:** alleen Top 10 | Tijdsplot | FM-detail + FM-evident-filter (alleen FM-detail).
- **Sub-rij Top 10:** label, bron-toggles, metric-combobox, horizon-segmented (*Per LCC-periode* | *Per jaar*), jaar-combobox (conditioneel), NB-weergave-segmented (*Uren* | *%*, conditioneel).
- Zichtbaarheid: sub-rij `visible ⇔ modus == bijdragen`; horizon/jaar/NB-toggles `visible ⇔ metric ∈ {faalmomenten, niet_beschikbaarheid}`; jaar-combobox `visible ⇔ horizon == per_year`; NB-weergave `visible ⇔ metric == niet_beschikbaarheid`.
- Kalenderjaren in combobox: afgeleid van `project.config.modeljaar` + `lifecycle_years` (zelfde mapping als LCC kalenderjaar).

### Scenariovergelijking

- Verwijder KPI-regel `risk_contribution` / label *Risicobijdrage* uit compare-service output.
- Pas compare-button-tooltip aan (geen “risico” als KPI in opsomming).

### Messages

- Nieuwe strings voor sub-balk, horizon-toggles, jaar-combobox (*Ø per jaar*), NB uren/%, tooltips (8760 u, gemiddelde vs enkel jaar).
- Verwijder/deprecate modus-placeholders NB/PM en PM-what-if-hint (niet meer getoond).

## Testing Decisions

**Goede tests** asserten op **waarden en zichtbaarheid**, niet op widget-hierarchie:

- Gegeven fixture-FM’s met bekende `expected_failures` en horizon_profile: lifecycle-totaal, gemiddelde per jaar, en één kalenderjaar produceren voorspelbare Top 10-ranking.
- NB: uren vs % en reconcile lifecycle vs som buckets (tolerantie zoals bestaande NB-proxy-tests).
- State-migratie: oude modus/metric strings map naar nieuwe defaults.
- pytest-qt (smoke): sub-balk alleen in Top 10; toggles verborgen bij Kosten; jaar-combobox alleen bij *per jaar*.

**Modules met tests (verplicht):**

| Module | Type |
|--------|------|
| **Contribution horizon value service** (nieuw) | Unit — bucket-math, edge cases (geen profile, scope) |
| **Contribution chart service** | Unit — ranking met nieuwe metrics/presentation |
| **Results workspace state** | Unit — migratie, sticky presentation |
| **Scenario compare service** | Unit — geen risico-regel meer |
| **Results workspace window** | pytest-qt smoke — sub-balk + toggle visibility |

**Prior art:** `tests/test_desktop_contribution_chart_service.py`, `tests/test_desktop_unavailability_chart_service.py`, `tests/test_slice32_workspace_ux_prios.py`, `tests/test_desktop_results_workspace_window.py`, `tests/test_desktop_scenario_compare_service.py`.

**Aanpassen/verwijderen:** tests die PM-modus, NB-modus, `METRIC_RISICO`, `METRIC_DOWNTIME`, `pm_submode` asserten.

## Out of Scope

- **Kans** (`p_ongewenste_gebeurtenis`) en **effectklassen** (`effect_bijdragen`) als aparte Top 10-metrics.
- **Verwijderen** `risk_contribution` uit `FMResult`, motor of project-JSON.
- **ValidateWindow** FM-resultatentabel uitbreiden met per-jaar kolommen (blijft lifecycle).
- **Tijdsplot** jaarselectie koppelen aan Top 10-jaarcombobox (bewust onafhankelijk; gemiddelde-default in Top 10).
- **Monte Carlo**, Excel-export, nieuwe effectklasse-UI.
- **Scenario CM/PM-run** afbouwen (alleen KPI-presentatie risico weg).
- **Slice 8** ValidateWindow-layout cleanup.

## Further Notes

### Relatie andere slices

| Slice | Relatie |
|-------|---------|
| 32 | Labels Top 10/Tijdsplot/Component — blijft; deze slice bouwt daarop |
| 31 | PM-modus alignment — modus verdwijnt; LCC/Tijdsplot blijft SSOT voor PM |
| 30 | KPI-inklap in Tijdsplot — ongewijzigd |
| 29/28 | LCC + what-if — blijven enige tijdreeks-modus |

### Risico’s

- **Bucket-proxy vs motor:** per-jaar faalmomenten/NB kan in randjaren afwijken van Monte Carlo; zelfde disclaimer-mentaliteit als NB-proxy (presentatie, geen motorwijziging).
- **Grote refactor tests:** veel workspace-modus-tests moeten worden herschreven, niet alleen genegeerd.
- **Presentatie-cache:** cache-keys moeten presentation-velden bevatten om stale Top 10 na toggle-wissel te voorkomen.

### Issues (gepubliceerd)

| # | Titel | Triage |
|---|--------|--------|
| 01 | Drie modi: NB/PM-modus volledig weg | done |
| 02 | Top 10-sub-balk + metrics zonder Risico/Downtime | done |
| 03 | Niet-beschikbaarheid Top 10: lifecycle, per jaar (Ø/jaar), uren/% | done |
| 04 | Faalmomenten Top 10: zelfde horizon/jaarkiezer | done |
| 05 | Presentatie-cache, messages, test-opruiming | done |

Keten: 01 → 02 → 03 → 04; 05 parallel na 03 (03 en 04 niet samengevoegd).
