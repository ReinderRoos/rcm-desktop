# PRD — RCM2 desktop slice 44 (Faalwijze bewerken in de resultatenwerkruimte)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage:** ready-for-agent  
**Type:** AFK + UI (adapter + werkruimte; beperkte `rcm_core` schema-registry)  
**Parent:** grill-me + architectuur-sessie 2026-05-23 (FM-detail editor)  
**Relatie:** slice 34 (read-only FM-verificatie), slice 7 (ValidateWindow faalwijzen-grid), slice 23 (resultatenwerkruimte)  
**Datum:** 2026-05-23

## Problem Statement

Reliability-analisten kunnen in de **resultatenwerkruimte** (modus FM-detail, slice 34) één faalwijze **controleren** — lifecycle-totalen, jaarreeksen, FM-invoerhash — maar **niet** de onderliggende motorinvoer wijzigen zonder het legacy **ValidateWindow** of handmatige JSON-bewerking.

Dat breekt de dagelijkse workflow: na een spot-check wil de analist **direct** faalmodel, effecttoekenningen, correctief scenario en preventief onderhoud bijstellen en **alleen de gewijzigde faalwijze(n)** opnieuw laten rekenen. ValidateWindow biedt wel een smal faalwijzen-grid (zes velden), maar geen geïntegreerd beeld van effectlinks, CM/PM-scenario’s, NMF, startleeftijd via PBS, of PM-taakgroepen — terwijl die invoer wél in de **FM-invoerhash** en de motor zit.

De **tabulaire editing-pipeline** en **Editing schema registry** dekken `faalwijzes`, `pm_tasks` en `effect_klassen` al gedeeltelijk; **FMEffectLink**, **PMEffectLink** en **TaskGroup** ontbreken in de registry, waardoor er geen eenduidig, testbaar pad is om de gevraagde tabs te materialiseren.

## Solution

Voeg een **modale faalwijze-editor** toe die opent bij **dubbelklik** op een FM-rij in modus **FM-detail** van de resultatenwerkruimte. De editor werkt op een **geïsoleerde EditingSession** (projectclone) met tabbladen:

1. **Basis** — faaltype (`random` / `aging` in v1), MTTF, sigma (bij aging), startleeftijd via gekoppeld PBS-`bouwjaar`, faalscenario-omschrijving, NMF (ja/nee ↔ `is_evident`), functie-FK.
2. **Effecten** — FM-effectlinks en PM-effectlinks voor taken van deze FM (IN, TST, REV, SVO), inclusief redundancy-fractie; bewerken van gekoppelde **effectklassen** (geen nieuwe klassen aanmaken in v1).
3. **Correctief** — CM-kosten (UI-gesplitst materiaal + arbeid/engineering → één `cost_cm_eur`), hersteltijd (`downtime_per_failure`), scenario-teksten (`notes`, `aanname_*`).
4. **Preventief** — CRUD op PM-taken van deze FM, PM-effectlinks, en inline bewerking van gekoppelde **taakgroepen** waar van toepassing.

**OK** valideert via de pipeline, materialiseert, schrijft het project atomisch weg (indien pad bekend), triggert **`run_incremental_analysis`** (`full_recompute=False`) zodat alleen faalwijzen met gewijzigde **FM-invoerhash** opnieuw rekenen, en ververst de werkruimte-presentatie. **Annuleren** gooit de sessie weg zonder persistente wijziging.

Ruggengraat: uitbreiding **Editing schema registry** + **`FmEditCommitService`** (Qt-vrij) als deep module; dunne **`FmEditorDialog`** in views.

## User Stories

### Toegang en workflow

1. Als analist wil ik in modus **FM-detail** op een faalwijzerij **dubbelklikken**, zodat de editor voor die FM opent.
2. Als analist wil ik de editor **niet** zien in Top 10 of Tijdsplot, zodat andere modi overzichtelijk blijven.
3. Als analist wil ik in de titelbalk van de editor **fm_id**, omschrijving en PBS/bouwdeel zien, zodat ik zeker ben van de juiste FM.
4. Als analist wil ik de editor **modaal** gebruiken, zodat ik niet per ongeluk de werkruimte wijzig terwijl ik bewerk.
5. Als analist wil ik met **Annuleren** alle wijzigingen verwerpen, zodat het geladen project ongewijzigd blijft.
6. Als analist wil ik met **OK** alleen doorgaan bij **geldige** invoer, zodat geen foute run start.
7. Als analist wil ik na **OK** alleen **gewijzigde** faalwijzen opnieuw berekend zien, zodat grote projecten snel blijven.
8. Als analist wil ik na opslaan de **FM-inspector** (slice 34) kunnen gebruiken om het effect te controleren, zodat bewerken en verifiëren in één venster samenkomen.

### Tab Basis — faalmodel en NMF

9. Als analist wil ik het **faaltype** kiezen tussen exponentieel (`random`) en veroudering (`aging`), zodat het model mijn aannames weerspiegelt.
10. Als analist wil ik **MTTF** (`mttf_jaar`) en bij aging **sigma** (`sigma_jaar`) bewerken, zodat faalmomenten kloppen.
11. Als analist wil ik **NMF** als ja/nee zien waarbij “ja NMF” betekent **niet merkbaar** (`is_evident=False`), zodat de UI aansluit op domeintaal.
12. Als analist wil ik de **faalscenario-omschrijving** (`faalwijze_omschrijving`, eventueel `eindgevolg`/`notes`) bewerken, zodat documentatie in het project blijft.
13. Als analist wil ik de **startleeftijd** beïnvloeden via **bouwjaar** van het gekoppelde PBS-item, zodat effectieve leeftijd in de motor klopt.
14. Als analist wil ik een **waarschuwing** als het PBS-item door meerdere FM’s gedeeld wordt, zodat ik weet dat bouwjaar-wijziging meer FM’s beïnvloedt.
15. Als analist wil ik de **functie** (`functie_id`) kunnen wijzigen via project-backed FK, zodat effecten bij de juiste functie hangen.
16. Als analist wil ik **repair_quality** kunnen zien/bewerken waar relevant voor CM/aging, zodat herstelkwaliteit meespeelt.

### Tab Effecten

17. Als analist wil ik **FM-effectlinks** (effect bij falen) zien en bewerken, inclusief **fractie** (redundancy), zodat gevolgkosten kloppen.
18. Als analist wil ik **PM-effectlinks** per PM-taak van deze FM bewerken, zodat IN/TST/REV/SVO-effecten traceerbaar zijn.
19. Als analist wil ik de gekoppelde **effectklasse** (omschrijving, `cost_gevolg_eur`, categorie) inline kunnen aanpassen, zodat ik geen los JSON-bestand nodig heb.
20. Als analist wil ik **geen nieuwe effectklasse** kunnen aanmaken in v1, zodat scope beheersbaar blijft en FK-chaos wordt vermeden.
21. Als analist wil ik bestaande links kunnen **toevoegen, wijzigen en verwijderen** binnen de FM-scope, zodat modellering compleet is.
22. Als analist wil ik **aanname_fractie** kunnen vastleggen, zodat redundancy-motivatie bewaard blijft.

### Tab Correctief

23. Als analist wil ik **CM-kosten** invoeren als **materiaal** + **arbeid/engineering** in de UI, zodat de kostenstructuur leesbaar is.
24. Als analist wil ik dat de motor nog steeds één **`cost_cm_eur`** ziet, zodat er geen schema-migratie nodig is.
25. Als analist wil ik **hersteltijd correctief** (`downtime_per_failure`, uren) bewerken, zodat downtime in resultaten klopt.
26. Als analist wil ik **scenario-tekst** (`notes`, `aanname_cm_kosten`, `aanname_downtime`) kunnen bijhouden, zodat aannames auditabel zijn.
27. Als analist wil ik **gevolgschade** via effectklassen (`cost_gevolg_eur`) kunnen meenemen, niet als apart CM-veld, zodat het domeinmodel consistent blijft.

### Tab Preventief

28. Als analist wil ik **PM-taken** van deze FM kunnen **toevoegen, wijzigen en verwijderen**, zodat het onderhoudsprogramma klopt.
29. Als analist wil ik per taak **type** (IN, TST, REV, SVO), interval, kosten en onbeschikbaarheid kunnen zetten, zodat PM-totalen kloppen.
30. Als analist wil ik een taak aan een **taakgroep** kunnen koppelen (`task_group_id`), zodat bundeling en deduplicatie werken.
31. Als analist wil ik **taakgroep-eigenschappen** (interval, kosten, duur) inline kunnen bewerken wanneer ik een groep selecteer, zodat gedeelde PM niet dubbel wordt ingevoerd.
32. Als analist wil ik **PM-effectlinks** per taak beheren, zodat PM-gevolgen consistent zijn met het effect-tabblad.
33. Als analist wil ik een waarschuwing zien als wijziging aan een taakgroep **andere FM’s** raakt, zodat ik gedeelde bundels bewust wijzig.

### Validatie, opslaan en run

34. Als analist wil ik **per-veld validatiefouten** in het Nederlands zien vóór opslaan, zodat ik fouten kan corrigeren.
35. Als analist wil ik dat **OK geblokkeerd** is bij openstaande validatiefouten, zodat geen inconsistent project wordt weggeschreven.
36. Als analist wil ik na succesvol opslaan een **incrementele analyse** (`full_recompute=False`), zodat alleen hash-gewijzigde FM’s opnieuw rekenen.
37. Als analist wil ik dat wijziging aan **gedeeld PBS bouwjaar** alle gekoppelde FM’s kan invalideren (hash-gedrag), zodat ik begrijp waarom meerdere FM’s herberekend worden.
38. Als analist wil ik dat de werkruimte **run-resultaat en presentatiecache** na commit ververst, zodat tabellen en inspector actuele cijfers tonen.
39. Als analist wil ik bij **geen bekend projectpad** alsnog in-memory kunnen committen en runnen, met duidelijke melding dat opslaan naar schijf ontbreekt, zodat exploratie mogelijk blijft.

### Architectuur en onderhoud

40. Als ontwikkelaar wil ik **views zonder `rcm_core`-imports** (behalve typing), zodat ADR UI/kern-decoupling geldt.
41. Als ontwikkelaar wil ik bewerklogica in **adapter deep modules** met **pytest** (niet pytest-gestuurd voor pure layout), zodat TDD op de seam blijft.
42. Als ontwikkelaar wil ik **FMEffectLink**, **PMEffectLink** en **TaskGroup** in de **Editing schema registry**, zodat één pipeline geldt voor alle tabs.
43. Als ontwikkelaar wil ik **`FmEditCommitService`** als smalle orchestratie (clone → apply bundles → validate → build → save? → incremental run → presentatie-invalidering), zodat UI en tests één entrypoint hebben.
44. Als ontwikkelaar wil ik **parity-tests** na schema-uitbreiding, zodat registry-velden niet driften van het domain model.
45. Als ontwikkelaar wil ik **FaalwijzenEditService** (slice 7) hergebruiken of consolideren, zodat er geen tweede bewerkcontracten voor dezelfde velden ontstaan.

### Relatie bestaande UI

46. Als analist wil ik **ValidateWindow** niet nodig hebben voor volledige FM-bewerking, zodat de werkruimte het standaardpad wordt.
47. Als analist wil ik dat het bestaande **faalwijzen-grid** in ValidateWindow blijft werken, zodat legacy-gebruikers niet breken.
48. Als trainer wil ik in documentatie lezen dat **bewerken** na slice 44 primair via FM-detail dubbelklik gaat, zodat cursusmateriaal klopt.

### Randgevallen

49. Als analist wil ik de editor niet kunnen openen **zonder geselecteerde FM**, zodat er geen lege dialoog ontstaat.
50. Als analist wil ik bij **run-fout** na opslaan het project **wel opgeslagen** houden met foutmelding, zodat invoer niet verloren gaat.
51. Als analist wil ik **dubbelklik** op een FM buiten actieve PBS-scope niet toestaan (zelfde scope als tabel), zodat consistentie behouden blijft.
52. Als analist wil ik **TimeDuration**-velden (downtime, PM-duur) in gebruiksvriendelijke eenheden (uren) zien, zodat ik geen JSON-structuur hoef te kennen.

## Implementation Decisions

### Modules (bouwen / wijzigen)

| Module | Rol |
|--------|-----|
| **Editing schema registry** | Nieuwe entiteiten `fm_effect_links`, `pm_effect_links`, `task_groups` met `field_types`, `required_fields`, `fk_rules` (schema-backed waar mogelijk; `functies` project-backed). Uitbreiding `faalwijzes` met ontbrekende bewerkbare velden (`downtime_per_failure` serialisatie, `repair_quality`, `eindgevolg`, `notes`, `aanname_*`) voor CM-tab. |
| **FmEditBundleService** (nieuw, Qt-vrij) | Laadt één FM-scope uit `RCMProject` naar rij-dicts per entiteit; past tab-wijzigingen toe op `EditingSession`; levert read-only **bundle view** voor dialog-tabs. |
| **FmEditCommitService** (nieuw, Qt-vrij) | Orchestratie: `EditingSession.clone_with_project` → apply bundles → `validate` → `build_project` → optioneel atomisch save → `run_incremental_analysis(full_recompute=False)` → invalideer presentatiecache / hydrate werkruimte via bestaande `RunService`-factory. Retourneert commit-resultaat (gewijzigde fm_ids, run-status, fouten). |
| **CmCostSplitMapper** (nieuw, Qt-vrij) | UI ↔ model: split `cost_cm_eur` in materiaal + arbeid voor weergave; som bij persist. Geen extra domain-velden in v1. Optioneel round-trip via `aanname_cm_kosten` tekstprefix of adapter-only sidecar in sessie (geen disk-schema). |
| **FaalwijzenEditService** | Consolideren: slice-7 grid blijft smal contract; FM-editor gebruikt volledige schema-velden via bundle/commit. Voorkom dubbele `EDITABLE_FIELDS`-lijsten — grid-delegates blijven subset. |
| **FmEditorDialog** (nieuw, view) | Modale `QDialog` met `QTabWidget`; tab-presenters alleen layout/bindings; roept adapter aan voor load/validate/commit. Geen businesslogica. |
| **Resultatenwerkruimte** | Dubbelklik-handler op FM-tabel in FM-detail; opent dialog met actief project + pad + geselecteerde `fm_id`; na commit refresh selectie/inspector. |
| **RunService / scenario-presentatie** | Hergebruik bestaande incremental-run seam; geen parallel policy-wijziging in deze slice. |

### Gedragscontracten

**EditingSession per dialoog**
- Bij open: `clone_with_project(actief_project)`.
- Bij annuleren: sessie verwerpen, parent-project onaangetast.
- Bij OK: `build_project` → parent vervangen door gebouwd project (in-memory) + save indien pad bekend.

**Faaltype v1**
- Alleen `FailureType.RANDOM` en `FailureType.AGING` in UI-keuzelijst.
- `falen op vraag` / `falen tijdens missie` **niet** in v1 (geen enum-wijziging).

**NMF-presentatie**
- Label “NMF”: **Ja** → `is_evident=False`; **Nee** → `is_evident=True`.

**Startleeftijd**
- Bewerk `bouwjaar` op het PBS-item van `faalwijze.pbs_id` via schema `pbs`.
- Waarschuwing als `count(faalwijzes metzelfde pbs_id) > 1`.

**Incrementele run na commit**
- `run_incremental_analysis(..., full_recompute=False)`.
- Hash-bepaling via bestaande `compute_fm_hash` / `find_affected_fms`; geen tweede definitie.
- Bewust risico: hash bevat volledige `pbs_items` — PBS-bouwjaar kan meerdere FM’s invalidieren; geen kern-refactor in v1 (optionele latere verbetering).

**Effecttab v1**
- CRUD op links; update bestaande `effect_klassen` rijen die via FK bereikbaar zijn.
- Geen “nieuwe effectklasse”-knop.

**PM-tab v1**
- CRUD `pm_tasks` gefilterd op `fm_id`; CRUD `pm_effect_links` voor die taken; inline `task_groups` voor geselecteerde groep.
- Waarschuwing bij taakgroep-wijziging die door andere FM’s wordt gerefereerd.

**Persist**
- Hergebruik atomische save-service met conflict-check wanneer project van schijf geladen is.
- Dirty-state werkruimte: markeer project gewijzigd na succesvolle commit (align met bestaande save/dirty-patronen waar aanwezig).

### Deep-module interfaces (conceptueel)

```python
@dataclass(frozen=True)
class FmEditBundle:
    fm_id: str
    faalwijze_row: dict
    pbs_row: dict  # gekoppeld item voor bouwjaar
    fm_effect_rows: tuple[dict, ...]
    pm_task_rows: tuple[dict, ...]
    pm_effect_rows: tuple[dict, ...]
    task_group_rows: tuple[dict, ...]  # alleen groepen bereikbaar vanuit pm_tasks
    effect_klasse_rows: tuple[dict, ...]  # FK-closure uit links

@dataclass(frozen=True)
class FmEditCommitResult:
    ok: bool
    errors: tuple[str, ...]
    affected_fm_ids: tuple[str, ...]
    run_result: RunResult | None  # None bij validatie/save-fout
```

```python
# CmCostSplitMapper — adapter-only, geen diskvelden
@dataclass(frozen=True)
class CmCostSplit:
    materiaal_eur: float
    arbeid_eur: float

def split_cm_cost(cost_cm_eur: float, hint: str | None = None) -> CmCostSplit: ...
def merge_cm_cost(split: CmCostSplit) -> float: ...
```

### Volgorde implementatie (aanbevolen)

1. Editing schema registry + parity-tests  
2. `FmEditBundleService` + `FmEditCommitService` (+ `CmCostSplitMapper`) met unit-tests  
3. `FmEditorDialog` + werkruimte-dubbelklik (pytest-qt smoke)  
4. Documentatie-update `CONTEXT.md` (bewerken vs verifiëren drie lagen)

## Testing Decisions

**Goede tests** controleren **gedrag aan de seam**: gevalideerde bundles materialiseren tot hetzelfde domain model als handmatig verwacht; commit triggert incremental run alleen voor hash-gewijzigde FM’s; UI toont validatiefouten en blokkeert OK — niet interne widget-structuur.

| Module | Testtype | Prior art |
|--------|----------|-----------|
| **Editing schema registry** | Parity unit | `tests/test_editing_schemas_parity.py` |
| **FmEditBundleService** | Unit — scope, FK-closure, filter op fm_id | `tests/test_desktop_faalwijzen_edit_service.py`, editing validation tests |
| **FmEditCommitService** | Unit — validate blokkeert; commit + patch `run_incremental_analysis` | `tests/test_architecture_deepening.py` (EditingSession), `tests/test_desktop_run_service.py` |
| **CmCostSplitMapper** | Unit — round-trip som | — |
| **FmEditorDialog / werkruimte** | pytest-qt smoke — dubbelklik opent; annuleren geen save; OK met fixture | `tests/test_desktop_results_workspace_window.py`, slice 34 FM-detail tests |

**Modules met verplichte tests:** registry parity, `FmEditCommitService`, `FmEditBundleService`, `CmCostSplitMapper`; pytest-qt minimaal één happy path + cancel.

**Geen verplichte view unit-tests** voor tab-layout; alleen smoke.

**Seam voor incremental run:** patch op `rcm_core.incremental_run` (projectconventie), niet op engine-internals.

## Out of Scope

- Nieuwe **FailureType**-waarden (falen op vraag, falen tijdens missie) en bijbehorende motorlogica.
- **Aanmaken** van nieuwe effectklassen vanuit de editor (alleen bestaande bewerken).
- **Volledige herberekening** als standaard na opslaan (`full_recompute=True` alleen handmatig/legacy).
- **ValidateWindow** als primair entrypoint; geen verwijdering legacy venster.
- **FM-hash verfijning** (alleen relevante PBS-slice i.p.v. volledige `pbs_items`) — optionele follow-up.
- **Monte Carlo**, scenario-vergelijker-UX, LTAP what-if vanuit deze editor.
- **Excel import/export** van FM-bundels.
- **CACHE_INPUTS_VERSION**-bump tenzij schema-wijziging motorinvoer-JSON wijzigt (registry-uitbreiding alleen editing, geen bump vereist indien geen `to_dict`-vormwijziging).
- **Parallel run policy** (slice 43-gebied).
- **Automatische verwachte-waarde** invoer of spreadsheet-sync.

## Further Notes

### Relatie andere slices

| Slice | Relatie |
|-------|---------|
| 34 | Read-only inspector wordt **post-edit** verificatiepad;zelfde FM-selectie |
| 7 | Smal faalwijzen-grid ValidateWindow blijft; deelt editing-pipeline |
| 23 | Host werkruimte en run-resultaat |
| 27 | NMF-semantiek (`is_evident`) moet consistent blijven in copy |
| 35 | Import blijft apart; geen RCM-Cost wizard in editor |
| 43 | Parallel dedup correct; editor assumeert bestaande PM-totalen-semantiek |

### Risico’s

| Risico | Mitigatie |
|--------|-----------|
| PBS `bouwjaar` invalidates veel FM’s via hash | UI-waarschuwing; toon `affected_fm_ids` na commit |
| Gedeelde **TaskGroup** wijziging | Waarschuwing + lijst andere FM’s metzelfde `group_id` |
| Presentatiecache stale na partial run | Commit-service roept bestaande cache-invalidate/hydrate aan |
| Dubbele bewerkcontracten slice 7 vs 44 | Consolideer veldlijsten; grid = subset |
| `downtime_per_failure` nested type in schema | Expliciete serialisatie in `field_types` / coercion in validation |

### Architectuur-kandidaten (uit sessie, niet alle verplicht in één PR)

- **FmEditCommitService** — verplicht in deze slice  
- **Registry-uitbreiding** — verplicht  
- **CmCostSplitMapper** — verplicht (klein)  
- **FaalwijzenEditService-consolidatie** — verplicht light  
- **FM-hash PBS-refinement** — bewust uitgesteld  

### Issues (gepubliceerd)

| # | Titel | Triage | Blocked by |
|---|--------|--------|------------|
| 01 | Editing schema registry + FM-edit commit seam | ready-for-agent | — |
| 02 | Modale editor: Basis + Correctief + dubbelklik werkruimte | ready-for-agent | 01 |
| 03 | Editor tab Effecten | ready-for-agent | 02 |
| 04 | Editor tab Preventief | ready-for-agent | 02 |
| 05 | Documentatie CONTEXT.md | ready-for-agent | 02 |

Afhankelijkheden: `01 → 02 → (03 ∥ 04) → 05` (05 kan parallel met 03/04 zodra 02 done).
