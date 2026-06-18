# PRD — RCM2 desktop slice 51 (verouderingsdistributies: normaal, links-afgeknipt normaal, Weibull 2p)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** AFK (motor + schema/validatie + UI + fixture)  
**Parent:** grill-me verouderingsmodellen 2026-05-27; slice 22/24 aging-SSOT; slice 42 Haarlem aging-fixture  
**Referentie-fixture:** `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json` (AWZI Haarlem Waarderpolder demo)  
**Referentiedocument:** NIST/AWZI-HWP faalmodeltabel (β-waarden per componenttype; MTTF = 1,2 × OLT)

## Problem Statement

De analist kan vandaag bij **verouderingsfalen** (`failure_type = aging`) alleen rekenen met een **volledige normaalverdeling** rond MTTF. In de praktijk (AWZI/HWP, NIST-referenties) worden ook **links-afgeknipte normaalverdelingen vanaf 0** en **2-parameter Weibull-verdelingen** (shape β, schaal η) gebruikt. De tool ondersteunt die keuzes niet: er is geen veld om het verouderingsmodel per faalwijze te kiezen, geen β-invoer, en geen bibliotheekdefaults uit de AWZI-componenttabel.

Gevolgen voor de analist:

- Faalmodellen die in rapportages als Weibull zijn onderbouwd, moeten worden **benaderd** met normaal + σ — met verkeerde LCC-vorm (wear-out vs symmetrisch rond MTTF).
- **Negative faalkans-massa** vóór leeftijd 0 is impliciet mogelijk bij de volledige normaal-CDF; dat is fysisch onwenselijk voor verouderingsmodellen die “vanaf installatie” starten.
- AWZI-β-waarden uit referentietabellen kunnen **niet** worden vastgelegd of hergebruikt via bibliotheek + faalwijze.
- Monte Carlo en analytisch pad zijn voor normaal **niet volledig consistent** bij startleeftijd *a* > 0; nieuwe verdelingen moeten wél meteen conditioneel correct zijn (R(t|a)), zonder de bestaande normaal-baselines stilletjes te breken.

## Solution

Introduceer een **subkeuze onder aging**: `aging_distribution` per faalwijze met drie waarden:

| Waarde | Betekenis |
|--------|-----------|
| `normal` | Huidig gedrag: volledige normaal-CDF (default bij ontbrekend veld) |
| `truncated_normal_0` | Normaalverdeling links-afgeknipt op interval **[0, ∞)** |
| `weibull_2p` | 2-parameter Weibull; invoer **MTTF + β**; η = MTTF / Γ(1 + 1/β) (niet opgeslagen) |

De motor (`distributions`-laag) krijgt een **testbare distributie-abstraktie** die cumulatieve faalkans, lifecycle-SSOT (faalmomenten per horizonbucket), en Monte Carlo-sampling dekt. Validatie **blokkeert runs** bij ongeldige Weibull-invoer. UI: **FM-editor** en **batch-grid** tonen verouderingsmodel + β alleen wanneer `failure_type = aging`. AWZI-tabel wordt **bibliotheekitems** (categorie faalmodel/verouderingsdefaults) plus een **beperkte subset** (~15–25) representatieve Haarlem-faalwijzen op Weibull gezet; overige aging-FM’s blijven `normal` voor stabiele regressie.

**Fase 1 (deze slice):** `normal` behoudt het bestaande analytische pad; `truncated_normal_0` en `weibull_2p` gebruiken het nieuwe pad inclusief R(t|a) bij *a* > 0. **Fase 2 (volgende slice):** universele conditionele SSOT ook voor `normal` + baseline-refresh.

## User Stories

### Domeinmodel en migratie

1. Als **analist**, wil ik per faalwijze een **verouderingsdistributie** kunnen kiezen, zodat het faalmodel aansluit bij mijn onderbouwing (normaal, links-afgeknipt, Weibull).
2. Als **analist**, wil ik dat bestaande projecten **zonder wijziging** blijven rekenen wanneer `aging_distribution` ontbreekt, zodat oude `.rcm.json`-bestanden en baselines niet stukgaan.
3. Als **analist**, wil ik bij Weibull **β (shape)** expliciet kunnen invoeren, zodat wear-out-steileid per componenttype vastligt.
4. Als **analist**, wil ik dat **η (schaal)** automatisch uit MTTF en β wordt afgeleid, zodat ik niet twee afhankelijke parameters hoef te onderhouden.
5. Als **analist**, wil ik **σ** kunnen gebruiken voor normaal én links-afgeknipt normaal, zodat de bestaande 15%-MTTF-regel bruikbaar blijft.
6. Als **analist**, wil ik dat **σ genegeerd wordt bij Weibull**, zodat er geen dubbelzinnige shape-parameters zijn.
7. Als **maintainer**, wil ik dat `failure_type = random` het bestaande exponentiële model blijft, zodat random vs veroudering een helder top-level onderscheid blijft.
8. Als **maintainer**, wil ik dat `aging_distribution` alleen semantisch actief is bij `failure_type = aging`, zodat random-FM’s geen spurious Weibull-velden hebben.

### Motor — distributiewiskunde

9. Als **analist**, wil ik dat **links-afgeknipt normaal** geen faalmassa vóór leeftijd 0 toekent, zodat het model fysisch klopt voor “vanaf installatie”.
10. Als **analist**, wil ik dat **Weibull 2p** een wear-out-vorm kan tonen (β > 1), zodat LCC-pieken later in de levensduur realistischer zijn dan symmetrisch normaal.
11. Als **analist**, wil ik dat bij **startleeftijd *a* > 0** truncated normal en Weibull **conditioneel** rekenen (survival R(t|a)), zodat assets die al oud zijn correct worden gemodelleerd.
12. Als **maintainer**, wil ik dat **`normal` in fase 1** het bestaande analytische pad behoudt, zodat slice 42 Haarlem-baselines stabiel blijven.
13. Als **maintainer**, wil ik dat **LCC/horizon-buckets** voor nieuwe verdelingen dezelfde SSOT-keten gebruiken als normaal (`expected_aging_lifecycle_faalmomenten_ssot`-equivalent), zodat LTAP/LCC niet divergeren.
14. Als **maintainer**, wil ik **Monte Carlo-sampling** voor alle drie aging-verdelingen, zodat `sample_time_to_failure` compleet blijft.
15. Als **maintainer**, wil ik een **MC-parity-test voor Weibull**, zodat analytisch vs sampling regressievangnet heeft.
16. Als **maintainer**, wil ik dat **REV-segmenten** en **repair_quality**-rejuvenation voor nieuwe verdelingen hetzelfde blijven werken als voor aging-normaal, zodat PM-verjonging niet stukgaat.

### Config — OLT → MTTF

17. Als **analist**, wil ik **`default_mttf_multiplier` per project** kunnen instellen, zodat AWZI (1,2 × OLT) en andere projecten (1,25) naast elkaar kunnen bestaan.
18. Als **maintainer**, wil ik default **1,25** behouden in code, zodat bestaande tests zonder expliciete config hetzelfde gedrag houden.
19. Als **trainer**, wil ik het Haarlem-demo-project optioneel op **multiplier 1,2** zetten, zodat het NIST/AWZI-referentiekader demonstreert.

### Bibliotheek — AWZI-defaults

20. Als **analist**, wil ik **bibliotheekitems** met AWZI-componentdefaults (β, MTTF-band, bron), zodat referentie-aannames centraal staan en niet per FM worden gekopieerd.
21. Als **analist**, wil ik een faalwijze via **`library_ref`** kunnen koppelen aan een bibliotheekitem, zodat documentatie (`aanname_faalmodel`) traceerbaar is.
22. Als **analist**, wil ik bibliotheekdefaults kunnen **overschrijven** op FM-niveau (`beta_jaar`, `aging_distribution`), zodat uitzonderingen mogelijk bl zijn.
23. Als **maintainer**, wil ik dat de motor **altijd FM-velden leest** (niet runtime-resolven uit bibliotheek), zodat cache-digest, tests en FM-editor eenduidig zijn.
24. Als **trainer**, wil ik in Haarlem **~15–25 representatieve FM’s** op Weibull + bibliotheek-ref, zodat de feature zichtbaar is zonder alle 121 aging-FM’s te migreren.

### Validatie en editing-pipeline

25. Als **analist**, wil ik een **validator-fout** wanneer `weibull_2p` zonder `beta_jaar > 0`, zodat incomplete invoer geen stille nul-faalmomenten geeft.
26. Als **analist**, wil ik validator-fouten **vóór run** zien in FM-editor en batch-grid, zodat ik niet eerst een lange run start.
27. Als **maintainer**, wil ik **editing schema registry**-parity voor nieuwe velden, zodat tabulaire editing-pipeline en domain model aligned blijven.
28. Als **maintainer**, wil ik **`CACHE_INPUTS_VERSION` bump** bij motorinvoer-wijziging, zodat incrementele cache niet verouderde FM-hashes hergebruikt.

### UI — FM-editor

29. Als **analist**, wil ik in de **faalwijze-editor** (basis-tab) een dropdown **verouderingsmodel** zien wanneer aging actief is, zodat ik het model per FM kan instellen.
30. Als **analist**, wil ik een **β-veld** zien bij Weibull, zodat shape expliciet invoerbaar is.
31. Als **analist**, wil ik **σ zichtbaar** bij normaal en links-afgeknipt normaal, en **verborgen/genegeerd** bij Weibull, zodat het formulier niet verwarrend is.
32. Als **analist**, wil ik verouderingsmodel-velden **verborgen** bij random falen, zodat het scherm overzichtelijk blijft.

### UI — batch-grid

33. Als **power user**, wil ik kolommen **verouderingsmodel** en **β** in het faalwijzen-batch-grid, zodat ik bulk-correcties kan doen (zoals bij failure_type/MTTF).
34. Als **power user**, wil ik dat kolom-zichtbaarheid **conditioneel** is op aging-rijen, zodat random-rijen geen lege Weibull-kolommen tonen die misleiden.

### Tests, baselines en regressie

35. Als **maintainer**, wil ik **unit-tests per distributie** (CDF, survival, η-afleiding), zodat wiskunde geïsoleerd testbaar is.
36. Als **maintainer**, wil ik dat **bestaande normaal/LCC-tests groen** blijven in fase 1, zodat slice 42/24-regressie intact is.
37. Als **maintainer**, wil ik **beperkte Haarlem-baseline-aanpassing** alleen waar Weibull-subset impact heeft, zodat niet het hele portfolio opnieuw getuned hoeft.
38. Als **maintainer**, wil ik **documentatie in CONTEXT** over fase-1 vs fase-2 conditionering, zodat analisten de bekende normaal/MC-split begrijpen tot fase 2.

### Developer ergonomie

39. Als **agent**, wil ik een **deep module** voor distributie-strategieën met smalle publieke API (`p_failure_by_age`, lifecycle SSOT, sampling), zodat motor-wijzigingen gelokaliseerd blijven.
40. Als **agent**, wil ik implementatievolgorde **motor → schema/validatie → UI → fixture**, zodat elke laag tegen groene tests bouwt.

## Implementation Decisions

### Scope en fasering

- **Slice 51 = fase 1:** drie `aging_distribution`-waarden; `normal` = legacy analytisch pad; truncated + Weibull = nieuw pad met R(t|a).
- **Fase 2 (aparte slice):** universele conditionele SSOT voor `normal` + Haarlem-baseline-refresh + MC-parity normaal.

### Deep modules (test-first waar mogelijk)

| Module | Rol | Interface (conceptueel) |
|--------|-----|-------------------------|
| **Aging distribution strategy** | Encapsuleert CDF, survival R(t), conditionele faalkans R(t\|a), lifecycle bucket-SSOT, MC sampling | Dispatch op `aging_distribution` + `(mttf, sigma, beta, current_age)` |
| **Weibull helpers** | η-afleiding, CDF, inverse CDF / sampling | `eta_from_mttf_beta(mttf, beta)`, `weibull_cdf(t, eta, beta)`, `weibull_survival(t, eta, beta)` |
| **Truncated normal [0,∞)** | Genormaliseerde Φ op [0,t]; conditionele mean voor lifecycle | Uitbreiding bestaande `normal_fast`-primitives; normalisatie-denominator Z = 1 − Φ(−μ/σ) |
| **Domain model (`Faalwijze`)** | Persistentie + effective helpers | Nieuwe velden; default `aging_distribution = "normal"`; `beta_jaar: float = 0.0` |
| **Editing schema + validation** | Tabulaire pipeline | Velden in `ENTITY_SCHEMAS["faalwijzes"]`; hard error `FM_WEIBULL_BETA_MISSING` |
| **UI adapter bindings** | Editor + grid | Conditionele kolommen/velden; geen directe `rcm_core`-imports in views |
| **AWZI bibliotheek seed** | Referentiedata | `BibliotheekItem`s met β/MTTF-band in `waarde`/`toelichting`; FM materialiseert naar `beta_jaar` |

### Schema-wijzigingen

**Faalwijze — nieuwe velden:**

```
aging_distribution: "normal" | "truncated_normal_0" | "weibull_2p"   # default "normal" bij deserialisatie
beta_jaar: float   # verplicht > 0 wanneer aging_distribution == "weibull_2p"
```

**Migratieregel:** ontbrekend `aging_distribution` ⇒ `"normal"`. Ontbrekend `beta_jaar` ⇒ `0.0` (alleen fout bij actieve Weibull).

**FailureType enum:** blijft `random` | `aging`; docstring AGING wordt generiek “verouderingsfalen” (niet meer “alleen normaal”).

**RCMConfig:** `default_mttf_multiplier` blijft bestaan; documenteer als **projectinstelbaar** (already in model); Haarlem-demo expliciet `1.2` indien gewenst.

**BibliotheekItem:** categorie `"faalmodel"` (bestaand) of documenteer subconventie in `waarde` voor AWZI-defaults, bijv. `"Weibull β=2.5; MTTF-band 12–15 jr"`. Geen gestructureerde JSON-velden op bibliotheek in v1 — seed naar FM bij fixture/import.

### Distributie-semantiek (normatief)

| Type | CDF F(t) | σ | β | Conditionering *a* > 0 (fase 1) |
|------|----------|---|---|----------------------------------|
| `normal` | Φ((t−μ)/σ) volledig | effective_sigma | n.v.t. | **Legacy pad** (ongewijzigd analytisch; MC conditioneel zoals nu) |
| `truncated_normal_0` | Φ(t)/Φ(∞) op [0,∞) | effective_sigma | n.v.t. | R(t\|a) = R(a+t)/R(a) |
| `weibull_2p` | 1 − exp(−(t/η)^β) | genegeerd | verplicht | R(t\|a) = R(a+t)/R(a) |

**Weibull schaal:** η = MTTF / Γ(1 + 1/β). MTTF blijft leidende invoer op faalwijze.

**Sigma:** `effective_sigma` (0 → 15% MTTF) voor beide normaal-varianten; motor negeert σ bij Weibull.

### Motor-integratie

- **`p_failure_by_age`:** uitbreiden met `aging_distribution` + `beta`; random-pad ongewijzigd.
- **`expected_aging_lifecycle_faalmomenten_ssot`:** dispatch naar per-type SSOT; `normal` = bestaande Φ-segmentlogica; truncated/Weibull = nieuwe segmentintegratie met R(t|a) en conditionele expected failure age.
- **`sample_time_to_failure`:** alle drie aging-types; Weibull via inverse CDF of rejection; truncated/normal via conditionele inverse CDF.
- **`CACHE_INPUTS_VERSION`:** verplicht bump (FM-invoerhash wijzigt).
- **Engine/horizon_profile:** leest `aging_distribution` + `beta_jaar` van `Faalwijze`; geen resolve uit bibliotheek at runtime.

### Validatie (hard blok)

Wanneer `failure_type == aging` en `aging_distribution == weibull_2p`:

- `beta_jaar` moet numeriek zijn en **> 0** → anders validator error, run geblokkeerd (CLI + adapter + UI).

Wanneer `failure_type == aging` en distributie is normaal-variant:

- Bestaande MTTF > 0 regels blijven; σ = 0 is toegestaan (fallback 15% via effective_sigma).

Wanneer `failure_type == random`:

- `aging_distribution` en `beta_jaar` worden genegeerd (niet gevalideerd als Weibull).

### UI-gedrag

- **FmEditorDialog (basis-tab):** dropdown verouderingsmodel; spinbox β; σ alleen bij normaal-varianten; alles disabled/hidden bij random.
- **FaalwijzenTableModel / batch-grid:** kolommen `aging_distribution` (enum labels NL: “Normaal”, “Links-afgeknipt normaal (0+)”, “Weibull 2p”) en `beta_jaar`; conditionele render/edit.
- **Bulk “pas bibliotheek-default toe”:** uitgesteld (volgende slice/issue).

### Fixture — Haarlem AWZI (fase 1 subset)

- Voeg **bibliotheekitems** toe met AWZI-HWP β/MTTF-referenties (componenttypes uit NIST-tabel).
- Zet **~15–25 representatieve aging-FM’s** op `weibull_2p` + `beta_jaar` + `library_ref`.
- Overige aging-FM’s: `aging_distribution` expliciet `normal` of veld weglaten (default).
- **Mapping:** Haarlem heeft lege `component_naam`; gebruik `bouwdeel_naam`/handmatige `library_ref`-lijst in fixture-issue (geen automatische PBS-string-lookup in v1).
- Optioneel: `config.default_mttf_multiplier = 1.2` in Haarlem-demo.
- **Baselines:** herzie alleen asserts die geraakt worden door Weibull-subset; geen volledige portfolio-flip.

### Architectuurprincipes (AGENTS.md)

- UI/kern-decoupling: views via adapter; distributie-wiskunde blijft in `rcm_core` (puur, geen Qt).
- Editing schema parity-test verplicht bij schema-wijziging.
- TDD op adapterlaag waar UI-bindings worden toegevoegd; kern-distributies test-first.

## Testing Decisions

### Wat maakt een goede test

- Test **extern gedrag** (CDF-waarden, som faalmomenten over lifecycle, CM-bucket-vorm, validator blok/allow), niet interne dispatch-implementatie.
- Gebruik **vaste numerieke tolerances**; vermijd flaky MC (voldoende N, seed).
- **Fase 1:** normaal-gedrag moet **bit-for-bit equivalent** blijven op bestaande fixtures waar geen nieuwe velden zijn gezet.

### Te testen modules

| Module | Testtype | Prior art |
|--------|----------|-----------|
| Weibull helpers (η, CDF, survival) | Unit, pure math | `tests/test_normal_fast.py`, `tests/test_distributions.py` |
| Truncated normal [0,∞) CDF | Unit | `tests/test_normal_fast.py` |
| `p_failure_by_age` dispatch | Unit | `tests/test_distributions.py` |
| Lifecycle SSOT truncated + Weibull | Unit + integratie | `tests/test_aging_monte_carlo.py`, slice 24 aging tests |
| Weibull MC parity | MC vs analytisch | `tests/test_aging_monte_carlo.py` (normaal parity) |
| Editing schema parity | Parity | `tests/test_editing_schemas_parity.py` |
| Validator Weibull β | Unit | `rcm_core/editing/validation` bestaande FM_MTTF tests |
| Haarlem subset fixture | Fixture assert | `tests/test_haarlem_fixture_aging_flip.py`, slice 42 characterization |
| UI adapter (grid/editor velden) | pytest-qt adapter | `tests/test_faalwijzen_table_model*.py`, FM editor adapter tests |

### Baseline-beleid

- **Geen** brede Haarlem-totalen-reset tenzij Weibull-subset meetbare KPI-shift veroorzaakt; documenteer delta in issue/fixture.
- **`normal`-only FM’s in Haarlem:** totalen moeten gelijk blijven aan pre-slice-51 (regressie-vangnet).

## Out of Scope

- **Fase 2:** universele R(t|a)-SSOT voor `normal` + volledige baseline-refresh.
- **Bulk-actie** “pas bibliotheek-default toe op selectie” in UI.
- **Gestructureerde velden** op `BibliotheekItem` (β als typed field); v1 gebruikt string `waarde` + materialisatie naar FM.
- **Volledige Haarlem-conversie** van alle ~121 aging-FM’s naar Weibull.
- **Automatische PBS→componenttype-mapping** zonder expliciete fixture-mappingtabel.
- **MC-parity-tests** voor truncated normal (optioneel later; Weibull parity is v1-doel).
- **Projectconfig-default** voor `aging_distribution` (nieuwe FM’s krijgen geen globale default truncated/Weibull).
- **Vervanging van `failure_type`** door één combined enum.
- **η opslaan** op faalwijze.
- **Globale wijziging** `default_mttf_multiplier` van 1,25 naar 1,2 voor alle projecten.
- **Isograph-import** uitbreiden voor Weibull (bestaande import kent wel `weibull` string maar geen RCM2 aging_distribution-pad — apart indien nodig).

## Further Notes

### Voorgestelde implementatievolgorde (tracer bullets)

1. **Motor-kern:** distributie-strategie + Weibull + truncated [0,∞) + unit tests + CACHE bump.
2. **Schema/validatie:** models, editing schemas, validator, parity test.
3. **UI:** FM-editor + batch-grid kolommen (adapter TDD).
4. **Fixture:** AWZI bibliotheek + Haarlem subset + gerichte baseline/fixture asserts.

### Bekende risico’s

- **Truncated normal lifecycle SSOT:** gesloten-vorm segmentintegratie moet net zo stabiel zijn als huidige Φ-SSOT (denominator Z → 0 bij extreme μ/σ).
- **Fase-1 inconsistentie normaal:** analytisch vs MC bij *a* > 0 blijft tot fase 2 — expliciet documenteren in CONTEXT en PRD-issue handoff.
- **Haarlem mapping:** zonder `component_naam` vereist subset-keuze **handmatige** FM-lijst in fixture-issue; geen inferentie uit bouwdeel_naam alleen.
- **LCC-vorm:** Weibull-subset kan portfolio-CM-vorm licht wijzigen; slice 42 shape-tests blijven geldig voor normaal-dominante mix.

### JSON-voorbeeld (Weibull-FM)

```json
{
  "failure_type": "aging",
  "aging_distribution": "weibull_2p",
  "mttf_jaar": 24.0,
  "beta_jaar": 2.5,
  "sigma_jaar": 0,
  "library_ref": "AWZI-BETA-POMP",
  "aanname_faalmodel": "Weibull 2p; β=2,5 (AWZI-HWP tabel); MTTF=1,2×OLT"
}
```

### Verwante slices

- **Slice 22/24:** aging lifecycle SSOT + normal_fast.
- **Slice 42:** Haarlem aging-dominantie + LCC-vormtests.
- **Slice 44/46:** FM-editor + batch-grid (UI landing zone).
- **Toekomst slice ~52:** aging conditional SSOT fase 2 (`normal` + baselines).
