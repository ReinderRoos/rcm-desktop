# PRD — Slice 73: NB-scalar reconciliatie & Effectfilter-leesbaarheid

**Status:** ready-for-agent
**Voorganger:** slice 71 (NB-effectfilter & metric 3-way), slice 72 (Top 10 UX-verfijning)
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van de architectuuranalyse (`/improve-codebase-architecture` + `/zoom-out`)
> op de twee door de gebruiker gemelde fricties. Geen interview — dit document
> codificeert wat al gediagnosticeerd is.

---

## Problem Statement

Een RCM-analist gebruikt de **Effectfilter** (`EffectNbFilterSet`) in de Bijdragen-modus
(Top 10) om de niet-beschikbaarheid (NB) van één of meer effectklassen te isoleren.
Twee dingen kloppen niet:

1. **Rekenkundig onmogelijk resultaat.** Een subselectie van één enkele
   NB-effectklasse levert een **hogere** NB-waarde op dan de **totale** NB met de
   filter leeg. Concreet observeerde de gebruiker in modus "Ø per jaar" een
   subselectie ("Ro…gd") rond 608k uur tegenover ~32k uur voor het hele project.
   Een deel kan per definitie nooit groter zijn dan het geheel; de analist
   verliest vertrouwen in elk Top 10-getal.

2. **Effectfilter is onleesbaar.** De combo heeft te weinig ruimte; de
   filterwaarden (effectklasse-omschrijvingen in de uitklaplijst) worden
   afgekapt ("Ro…gd"), zodat de analist niet ziet wat hij aan- of uitvinkt.

## Solution

Vanuit de gebruiker gezien:

- **Het geheel is altijd ≥ de delen.** De NB van een subselectie is nooit groter
  dan de totale NB, en de som van alle losse effectklassen sluit (op een
  gedocumenteerde, voorspelbare manier) aan op de totale NB. Of de filter nu leeg
  of gevuld is, hetzelfde getal wordt op dezelfde manier berekend en in dezelfde
  eenheid en horizon getoond ("uren" vs "%", "Ø per jaar" vs "levensduur" vs een
  specifiek kalenderjaar).

- **De analist kan de filterwaarden lezen.** De Effectfilter en zijn uitklaplijst
  zijn breed genoeg om de volledige effectklasse-omschrijving te tonen (of tonen
  een volledige tooltip), zodat selecteren betrouwbaar is.

---

## Zoom-out: modulekaart (domein- + architectuurvocabulaire)

De NB-scalar wordt vandaag op **twee** plekken berekend met **divergente**
implementaties — dat is de kern van de bug.

```
                          Bijdragen-modus (Top 10)
                                   │
              rcm_desktop/adapter/contribution_chart_service.py
                       build_contribution_rows()
                                   │
                        _fm_contribution_value()
                          /                     \
            filter LEEG (is_all)            filter GEVULD
                   │                              │
   contribution_horizon_value_service     effect_impact_service
        contribution_value_for_fm()           nb_scalar_for_fm()
        → _unavailability_scalar()            → _filtered_nb_scalar()
        (Pad A: Ø per jaar = gemiddeld)       (Pad B: via _effect_presentation
                                               → horizon "lifecycle" = TOTAAL)
```

Betrokken modules (domeintaal → bestand):

- **Effectimpact-deepmodule** — `rcm_core/effect_impact_service.py`
  (`EffectNbFilterSet`, `EffectPresentation`, `aggregate`, `nb_scalar_for_fm`,
  `nb_yearly_series`, `_total_nb_scalar`, `_filtered_nb_scalar`,
  `_present_values`). Qt-vrij; **de enige plek die categorie-formules toepast.**
- **Top 10 horizonwaarde-adapter** — `rcm_desktop/adapter/contribution_horizon_value_service.py`
  (`contribution_value_for_fm`, `_unavailability_scalar`, `_nb_hours_per_bucket`).
- **Top 10 aggregatie-adapter** — `rcm_desktop/adapter/contribution_chart_service.py`
  (`build_contribution_rows`, `_fm_contribution_value`, **`_effect_presentation`**).
- **Effectfilter-widget** — `rcm_desktop/views/widgets/nb_effect_filter_combo.py`
  (`NbEffectFilterCombo`).
- **Werkruimte-venster** — `rcm_desktop/views/results_workspace_window.py`
  (`_build_top10_subbar`, plaatsing van de combo).

---

## Diagnose (root cause)

### Bug 1 — `average` → `lifecycle` mapping (de ~60×)

In `rcm_desktop/adapter/contribution_chart_service.py` zet `_effect_presentation`
bij een actieve filter de keuze `year_choice == "average"` om naar
`horizon = "lifecycle"`:

```text
if pres.year_choice == "average":
    return EffectPresentation(horizon="lifecycle", ...)
```

Gevolg: bij **gevulde** filter levert `_filtered_nb_scalar` de **levensduur-totale**
NB (som van `fm_effect_bijdragen` over de hele horizon × `downtime_hr`), terwijl het
**lege**-filterpad (`_unavailability_scalar`) bij "Ø per jaar" netjes
`sum(buckets) / len(buckets)` = **gemiddelde jaarwaarde** teruggeeft. Het verschil is
ongeveer `ltap_horizon_bucket_count(lifecycle_years)` (vaak ~60). Dit verklaart de
608k vs 32k-observatie.

### Bug 2 — twee paden, één concept (geen locality)

Lege vs gevulde filter lopen door **fysiek verschillende** implementaties
(`contribution_value_for_fm` vs `nb_scalar_for_fm`). Ze kunnen daardoor niet
consistent zijn, ook niet na het repareren van Bug 1:

- **Verborgen NB / detectievertraging.** Pad A telt
  `expected_total_downtime_hr` (incl. detectievertraging/hidden NB) + PM-downtime.
  Pad B somt alleen `fm_effect_bijdragen × downtime_per_failure` per klasse —
  **zonder** hidden NB en **zonder** detectievertraging. De delen sommeren dus niet
  naar het geheel.
- **PM in verkeerde eenheid.** ~~In `_present_values` (categorie beschikbaarheid)
  wordt `cm_val = cm_raw * downtime_hr` (uren), maar `pm_val = pm_raw` (een
  telling, geen uren).~~ **Weerlegd bij implementatie (2026-06-11):** `engine.py`
  schrijft `pm_effect_bijdragen` al in uren (`duration.to_hours() × RF ×
  executions`); `pm_val = pm_raw` was dus al correct. Geen codewijziging nodig;
  alleen de CM-telling vereist `× downtime` (per FM — zie Bug 3).
- **RF-fractie-partitie.** De som van RF-fracties over availability-effectklassen
  van één FM hoeft geen 1,0 te zijn (kan >1 zijn). Daardoor kan de som van
  losse-klasse-NB groter zijn dan de fysieke CM-downtime van de FM.

### Bug 3 — latente per-FM `downtime_hr` in `aggregate`

In `rcm_core/effect_impact_service.py` zet `aggregate` `downtime_hr` per klasse
**eenmalig** vast (de `setdefault`-bucket) op de waarde van de **eerste** FM die
die klasse raakt, terwijl `cm_raw` over **alle** FM's accumuleert:

```text
bucket = raw.setdefault(klasse_id, {"cm_raw": 0.0, "pm_raw": 0.0, "downtime_hr": downtime_hr})
bucket["cm_raw"] += fm_cm.get(klasse_id, 0.0)   # accumuleert over FM's
# downtime_hr blijft die van de éérste FM
```

Bij `_filtered_nb_scalar` bijt dit niet (aanroep met één FM), maar in de
**Effectimpact-tabel** (`aggregate` over meerdere FM's met verschillende
`downtime_per_failure`) levert het een fout uur-getal.

### UX — Effectfilter-breedte

`NbEffectFilterCombo` (`rcm_desktop/views/widgets/nb_effect_filter_combo.py`) zet
geen `setMinimumContentsLength`/`setSizeAdjustPolicy`, en in
`results_workspace_window.py` (`_build_top10_subbar`) wordt de combo zonder
breedte-constraint aan de `QHBoxLayout` toegevoegd. Slice 72 issue 00 loste het
**openen** bij klik op, maar niet de **leesbaarheid**: de gesloten combo én de
popup-items worden afgekapt.

---

## User Stories

**Correctheid — geheel ≥ delen**

1. Als RCM-analist wil ik dat een subselectie van NB-effectklassen nooit een hogere
   NB toont dan de totale NB (filter leeg), zodat ik de cijfers vertrouw.
2. Als analist wil ik dat de NB-waarde van de filter in dezelfde horizon ("Ø per
   jaar", "levensduur", of een kalenderjaar) wordt berekend als de totale NB, zodat
   ik appels met appels vergelijk.
3. Als analist wil ik dat een enkele geselecteerde effectklasse in "Ø per jaar" een
   gemiddelde jaarwaarde toont (niet een levensduur-totaal), zodat het getal klopt
   met de as-eenheid.
4. Als analist wil ik dat de som van alle selecteerbare NB-posten (effectklassen +
   Detectie-/verborgen-NB-restpost) exact gelijk is aan de totale NB, zodat het
   geheel aantoonbaar uit de delen volgt.
5. Als analist wil ik dat verborgen NB / detectievertraging als een aparte,
   selecteerbare **restpost** in de effectfilter staat, zodat ik die downtime kan
   in- of uitsluiten en er geen onverklaard gat tussen geheel en delen zit.
5b. Als analist wil ik dat "alle posten aangevinkt" exact het totaal oplevert en
   "niets aangevinkt" eveneens het totaal (slice 33-semantiek), zodat de uitersten
   van de filter consistent zijn.
6. Als analist wil ik dat de NB consistent in "uren" of "%" wordt getoond ongeacht
   of de filter leeg of gevuld is, zodat de eenheid betrouwbaar is.
7. Als analist wil ik dat een subselectie per kalenderjaar (bijv. 2030) net als de
   totale NB de jaar-bucketwaarde teruggeeft, zodat jaarvergelijkingen kloppen.
8. Als analist wil ik dat de NB in "%" gefilterd correct relateert aan de jaar-uren
   (8760 u) respectievelijk de levensduur-uren, zodat percentages consistent zijn.

**Effectimpact-tabel (Bug 3)**

9. Als analist wil ik dat de Effectimpact-tabel per effectklasse correcte uren toont
   wanneer meerdere faalwijzen met verschillende `downtime_per_failure` bijdragen aan
   dezelfde klasse, zodat de tabel niet stilletjes verkeerd rekent.

**Effectfilter-leesbaarheid**

10. Als analist wil ik dat de Effectfilter-combo breed genoeg is om de gesloten
    samenvatting te tonen, zodat ik de actieve selectie herken.
11. Als analist wil ik dat de uitklaplijst de volledige effectklasse-omschrijving
    toont (of een volledige tooltip), zodat ik weet wat ik aanvink.
12. Als analist wil ik dat de Effectfilter zijn ruimte behoudt naast de andere
    toolbar-elementen, zodat hij niet wordt platgedrukt bij smalle vensters.

**Vertrouwen / regressie**

13. Als analist wil ik dat de bestaande lege-filter Top 10-getallen niet veranderen
    door deze fix (behalve waar ze fout waren), zodat ik geen onverwachte verschuiving
    in mijn rapportage zie.

---

## Implementation Decisions

### Seam-keuze (deepening)

- **De NB-bucketreeks (per FM) is de enige bron-van-waarheid (Optie C, besloten).**
  Eén interne spine bouwt per FM én per `EffectNbFilterSet` de gepresenteerde NB
  per horizonbucket. Zowel `nb_scalar_for_fm` (reductie: levensduur-som /
  jaargemiddelde / één kalenderjaar) als `nb_yearly_series` (de reeks zelf)
  reduceren/presenteren uit die spine. Het publieke oppervlak blijft ongewijzigd.
  Deletion-test: verwijder de spine en de bucketlogica herverschijnt in de
  Top 10-scalar, de Tijdsplot én de leeg/gevuld-varianten — sterke keep.
  Invarianten die er gratis uit volgen: *Top 10-scalar = reductie van de
  Tijdsplot-curve* en *deelselectie ≤ totaal*.

- **`contribution_chart_service._fm_contribution_value` routeert NB altijd via
  `nb_scalar_for_fm`** (ook bij `is_all()` → lege `EffectNbFilterSet`).
  `contribution_value_for_fm` blijft bestaan voor de niet-NB-metrics
  (kosten, faalmomenten).

- **`_effect_presentation` mag `year_choice` niet platslaan.** De mapping
  `ContributionPresentation → EffectPresentation` moet `"average"` doorgeven als
  een "per_year/average"-intentie, niet als `"lifecycle"`. De gemiddelde-jaar-
  semantiek die `_unavailability_scalar` vandaag heeft, wordt door de spine
  gedeeld voor zowel het lege als het gevulde pad.

- **Reconciliatie-contract (delen → geheel) — besloten:**
  - **Verborgen NB als selecteerbare restpost (1a).** De NB-effectfilter krijgt
    een extra, selecteerbare **Detectie-/verborgen-NB-restpost** naast de echte
    availability-effectklassen. De selecteerbare verzameling vormt zo een **echte
    partitie** van de totale NB: leeg = totaal, alles aangevinkt = totaal, elke
    deelselectie ≤ totaal. De echte effectklassen behouden hun definitie
    (`RF × downtime × failures` + PM-uren); de restpost absorbeert
    detectievertraging (+ eventueel niet-toegewezen PM).
  - **RF niet hernormaliseren (2b).** Motor-RF blijft eerlijk; de invariant wordt
    geborgd door de partitie + een **veiligheids-clamp** (getoonde filterwaarde
    ≤ totaal) voor zeldzame RF-overlap (Σ RF > 1).
  - **PM-eenheid (2c, fix).** In het availability-pad moet de PM-bijdrage in
    **uren** zijn (gedegradeerde uren, conform `CONTEXT.md`), niet als telling.

- **Bug 3 (`aggregate`):** bereken `downtime_hr` per FM en accumuleer
  `cm_raw × downtime_hr` (uren) per FM, in plaats van `cm_raw` te accumuleren en
  pas later met één `downtime_hr` te vermenigvuldigen. Houd `_filtered_nb_scalar`
  (één FM) gedragsneutraal.

- **Effectfilter-UX (views, niet test-first per AGENTS.md):**
  - `NbEffectFilterCombo`: `setSizeAdjustPolicy(AdjustToContents)` +
    `setMinimumContentsLength(...)`; popup-view breedte op de langste
    klasse-omschrijving; per item een tooltip met de volledige omschrijving.
  - `_build_top10_subbar`: geef de combo een redelijke `minimumWidth` /
    stretch-factor zodat hij niet wordt platgedrukt.

### Architectuurprincipes (AGENTS.md)

- UI/kern-decoupling blijft: views raken de kern alleen via adapters.
- Kern (`rcm_core`) blijft Qt-vrij.
- Bij motorwijziging zonder JSON-vormwijziging: verhoog `CACHE_INPUTS_VERSION` in
  `rcm_core/cache.py` (NB-scalar-semantiek wijzigt de afgeleide presentatie, niet
  per se de JSON-vorm — controleer of een cache-bump nodig is).

---

## Testing Decisions

Goede tests toetsen **extern gedrag** aan de seam, niet de implementatie.

- **Primaire seam: de NB-bucketreeks-spine + `nb_scalar_for_fm` (Qt-vrij, `rcm_core`).**
  Test-first:
  1. **Geheel ≥ delen-invariant:** voor een FM met meerdere NB-posten geldt voor
     elke deelselectie `nb_scalar_for_fm(filter=subset) ≤ nb_scalar_for_fm(filter=leeg)`,
     voor elke presentation (Ø per jaar / levensduur / kalenderjaar; uren / %).
  2. **Partitie-pariteit:** lege filter = "alle posten geselecteerd (incl.
     Detectie-/verborgen-NB-restpost)" = totaal, per presentation. En Σ van de
     losse posten = totaal.
  3. **Geen 60×:** "Ø per jaar" gefilterd ≈ levensduur-totaal / aantal buckets.
  4. **Spine-consistentie:** Top 10-scalar = reductie van de bucketreeks die de
     Tijdsplot tekent (`sum`/`avg`/`[jaar]` over `nb_yearly_series`-buckets),
     voor leeg én gevuld.
- **Aggregate (Bug 3):** test `aggregate` over **twee** FM's met verschillende
  `downtime_per_failure` die dezelfde klasse raken → verwachte uren = som van
  per-FM `cm_raw × downtime_hr`.
- **Adapter-seam: `build_contribution_rows`** (pytest-qt-vrij waar mogelijk):
  ranking en waarden veranderen niet voor het lege-filterpad t.o.v. golden
  (behalve gecorrigeerde fouten); gevulde filter produceert waarden ≤ totaal.
- **Prior art:** bestaande tests rond `effect_impact_service` (slice 70/71) en
  `contribution_*`-adapters; volg dezelfde fixtures. Gebruik indien beschikbaar de
  Gaarkeuken/Haarlem-fixture om de ~60×-hypothese numeriek te bevestigen vóór de
  fix (read-only baseline).
- **UX:** geen test-first (pure views per AGENTS.md); handmatige verificatie van
  combo-breedte en tooltips.

---

## Out of Scope

- Top 10 UX-items die slice 72 al dekt (dropdown openen, chart-only, staaflabels,
  bron-toggle, display-seam).
- Tijdsplot-/grafiekwijzigingen (slice 71).
- Nieuwe metrics, nieuwe effectcategorieën of nieuwe bronnen.
- Kostendiagnose en niet-NB-metrics in `contribution_value_for_fm`.
- Wijzigingen aan de RCM-motor (`engine.py`) zelf, tenzij de reconciliatie geen
  andere weg laat (dan: aparte beslissing + cache-bump).

## Further Notes

- De volgorde van werken: eerst een **read-only baseline** draaien op een fixture
  om het feitelijke verschil-factor te printen en de ~60×-hypothese te bevestigen;
  daarna test-first Bug 1 → Bug 2 (reconciliatie-contract) → Bug 3 → UX.
- Het reconciliatie-contract (RF-partitie + verborgen NB) is vastgelegd in
  **ADR-0010** (NB-reconciliatie — bucketreeks-spine + verborgen-NB-restpost) en in
  `CONTEXT.md` (termen **NB-bucketreeks (per FM)** en
  **Detectie-/verborgen-NB-restpost**).
- Voorgestelde tracer-bullet-issues:
  1. Baseline read-only: print verschil-factor lege vs gevulde filter (bevestig 60×).
  2. NB-bucketreeks-spine (Optie C): één interne bouwer per FM/filter; `nb_scalar_for_fm`
     en `nb_yearly_series` reduceren/presenteren eruit; `_effect_presentation` geeft
     "Ø per jaar" door (Bug 1). Spine-consistentie- + geen-60×-tests.
  3. Reconciliatie-contract: Detectie-/verborgen-NB-restpost als selecteerbare post
     in `EffectNbFilterSet`/effectfilter; RF niet hernormaliseren + clamp; PM-eenheid
     naar uren. Partitie- + invariant-tests.
  4. Bug 3: per-FM `downtime_hr` in `aggregate`; tests met 2 FM's.
  5. Effectfilter-UX: combobreedte, popup-breedte, tooltips (incl. restpost-regel).
