# PRD — RCM2 desktop slice 52 (Modelinstellingen-dialoog)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** AFK (kern + adapter + werkruimte-UI)  
**Parent:** grill-me Modelinstellingen 2026-05-27; slice 51 (aging-distributies); slice 44 (FM-editor commit-patroon)  
**Relatie:** slice 23 (resultatenwerkruimte), slice 7 (faalwijzen batch-grid), slice 35 (Isograph-import metadata)

## Problem Statement

Projectbrede instellingen — LCC-periode, modeljaar, verouderingsdefaults, standaard faalparameters, projectmetadata — zijn vandaag **verspreid** over JSON-handmatig bewerken, impliciete code-defaults, of per-faalwijze schermen (FM-editor, faalwijzen batch-grid). Er is **geen centraal dialoog** waar een analist in één keer ziet en wijzigt wat het hele model drijft.

Gevolgen:

- **`lifecycle_years`** en **`modeljaar`** staan wel in `RCMConfig`, maar zijn niet vanuit de desktop-UI bereikbaar; wijziging vereist JSON of externe tooling.
- **`default_sigma_fraction`** en **`default_mttf_multiplier`** staan in config, maar **`effective_sigma`** negeert de config nog (hardcoded 15% × MTTF) — het veld is misleidend als het ooit zichtbaar wordt zonder fix.
- **`aging_distribution`** is per faalwijze (slice 51), maar er is geen **projectdefault** + bulk-toepassing voor aging-FM’s.
- **`projectnaam`** en **`modelleur`** ontbreken op het domain model; import-metadata zit alleen onder `import_settings["isograph_project"]` — niet bruikbaar voor rapportages.
- **`failure_type`** hoort **niet** in dit scherm (bewuste keuze), maar analisten verwachten soms een “globaal faaltype” — dat moet duidelijk **afwezig** blijven ten gunste van FM/batch-paden.
- **Monte Carlo** (`monte_carlo_n`, seed) staat in config/validators, maar desktop-MC-run is nog toekomst — velden zijn onzichtbaar terwijl ze al in fixtures leven.
- **Horizon-bucketinterval** is afgeleid (1 kalenderjaar via `ltap_horizon_bucket_count`); gebruikers zoeken een “interval”-veld dat niet bestaat — verwarring zonder read-only uitleg.

## Solution

Voeg een **Modelinstellingen**-dialoog toe, bereikbaar via een knop in de **resultatenwerkruimte**-toolbar. Het dialoog groepeert projectbrede velden in secties/tabs:

| Sectie | Inhoud |
|--------|--------|
| **Project** | `projectnaam`, `modelleur` |
| **Horizon & tijd** | `lifecycle_years` (LCC-periode), `modeljaar`, read-only “bucket-interval: 1 jaar” |
| **Veroudering (defaults)** | `default_aging_distribution`, `default_beta_jaar` (conditioneel), knop **“Toepassen op alle aging-faalwijzen”** |
| **Standaard faalparameters** | `default_mttf_multiplier`, `default_sigma_fraction` |
| **Monte Carlo** | `monte_carlo_n`, `monte_carlo_seed` — **disabled** + tooltip “nog niet actief in desktop” |

**OK** werkt project bij in sessie, **slaat atomisch op** wanneer een pad bekend is (zelfde patroon als FM-editor), markeert **herbereken vereist** bij motorrelevante wijzigingen, en biedt optioneel **Direct herberekenen** (default uit). **Apply aging** is een **expliciete** actie vóór OK — zonder Apply blijven bestaande faalwijzen ongewijzigd; alleen config-defaults worden opgeslagen.

Ruggengraat: Qt-vrije **`model_settings_service`** (+ commit/save helper) als deep module; dunne **`ModelSettingsDialog`** in views; kernwijzigingen beperkt tot serialisatie, validators, en **`effective_sigma`-koppeling**.

## User Stories

### Toegang en workflow

1. Als **analist**, wil ik vanuit de **resultatenwerkruimte** op **Modelinstellingen** klikken, zodat ik projectbrede parameters op één plek kan beheren zonder JSON te editen.
2. Als **analist**, wil ik het dialoog **niet** in ValidateWindow of losse menu’s, zodat er één canoniek entrypoint is zonder drift.
3. Als **analist**, wil ik dat het dialoog **alleen opent** wanneer een project geladen is, zodat ik geen lege instellingen bewerk.
4. Als **analist**, wil ik vóór openen een **dirty-guard** op het faalwijzen batch-grid (zelfde patroon als FM-editor), zodat ik geen conflicterende onopgeslagen grid-wijzigingen verlies.
5. Als **analist**, wil ik in de titelbalk **“Modelinstellingen — {projectnaam of bestandsnaam}”** zien, zodat context duidelijk is.
6. Als **analist**, wil ik met **Annuleren** alle wijzigingen in het dialoog verwerpen, zodat het geladen project ongewijzigd blijft.
7. Als **analist**, wil ik met **OK** alleen doorgaan bij **geldige** invoer (validators), zodat geen inconsistent project wordt opgeslagen.
8. Als **analist**, wil ik na **OK** het project **direct op schijf** zien wanneer een pad bekend is, zodat wijzigingen niet verloren gaan bij crash.
9. Als **analist**, wil ik na motorrelevante wijzigingen een **“herbereken vereist”**-indicatie, zodat ik weet dat presentatie/cache verouderd is.
10. Als **analist**, wil ik optioneel **Direct herberekenen** aanvinken (default uit), zodat ik zelf kies tussen snel opslaan en meteen verversen.
11. Als **analist**, wil ik dat **alleen projectnaam/modelleur** wijzigen **geen** herberekening vereist, zodat metadata snel bij te werken is.

### Sectie Project — metadata

12. Als **analist**, wil ik **projectnaam** kunnen invoeren en opslaan, zodat rapportages later een leesbare titel hebben.
13. Als **analist**, wil ik **modelleur** kunnen invoeren, zodat eigenaarschap van het model traceerbaar is.
14. Als **analist**, wil ik dat lege metadata **geen** validatiefout geeft, zodat bestaande projecten soepel migreren.
15. Als **analist**, wil ik na **Isograph-import** automatisch **projectnaam** vooringevuld zien (uit Description/bestandsnaam) wanneer het veld leeg was, zodat ik niet opnieuw hoef te typen.
16. Als **maintainer**, wil ik dat projectnaam/modelleur **niet** in globale digest / FM-hash zitten, zodat metadata-wijziging geen onnodige herberekening triggert.

### Sectie Horizon & tijd

17. Als **analist**, wil ik **LCC-periode** (`lifecycle_years`) kunnen wijzigen, zodat horizon en jaarbuckets aansluiten op mijn analysevenster.
18. Als **analist**, wil ik **modeljaar** kunnen wijzigen, zodat kalenderjaren in LCC/Tijdsplot kloppen zonder bouwdelen aan te passen.
19. Als **analist**, wil ik **read-only** zien dat het **bucket-interval 1 kalenderjaar** is, zodat ik niet zoek naar een apart interval-veld.
20. Als **analist**, wil ik begrijpen dat lifecycle het **aantal horizonbuckets** bepaalt (via `ltap_horizon_bucket_count`), zodat LCC en LTAP consistent blijven.
21. Als **analist**, wil ik na wijziging lifecycle/modeljaar **herbereken vereist**, zodat oude run-resultaten niet stilletjes verkeerd lijken.

### Sectie Veroudering (defaults)

22. Als **analist**, wil ik een **projectdefault voor verouderingsdistributie** kiezen (`normal`, `truncated_normal_0`, `weibull_2p`), zodat nieuwe defaults consistent zijn met slice 51.
23. Als **analist**, wil ik bij default **Weibull 2p** een **default β** (`default_beta_jaar`) invoeren, zodat shape projectbreed vastligt.
24. Als **analist**, wil ik dat **random-faalwijzen** niet worden geraakt door verouderingsdefaults, zodat exponentiële FM’s intact blijven.
25. Als **analist**, wil ik op **“Toepassen op alle aging-faalwijzen”** klikken en een **teller** zien (bijv. “42 aging-faalwijzen”), zodat ik de impact begrijp vóór overschrijven.
26. Als **analist**, wil ik **bevestiging** vóór bulk-apply, zodat per-FM uitzonderingen bewust worden overschreven.
27. Als **analist**, wil ik dat **Apply** `aging_distribution` en `beta_jaar` op aging-FM’s zet volgens de huidige default-waarden in het dialoog, zodat bulk en defaults synchroon zijn.
28. Als **analist**, wil ik **zonder Apply** alleen config-defaults opslaan, zodat bestaande per-FM keuzes behouden blijven tot ik expliciet toepas.
29. Als **analist**, wil ik **`failure_type` niet** in dit dialoog, zodat faaltype per FM/batch blijft (FM-editor + faalwijzen grid).
30. Als **maintainer**, wil ik validatie op default β (> 0 bij Weibull-default), zodat ongeldige config geen run start.

### Sectie Standaard faalparameters

31. Als **analist**, wil ik **`default_mttf_multiplier`** kunnen wijzigen (bijv. 1,25 vs 1,2 AWZI), zodat PBS-MTTF-defaults projectbreed kloppen.
32. Als **analist**, wil ik **`default_sigma_fraction`** kunnen wijzigen, zodat FM’s met `sigma_jaar = 0` de gekozen fractie gebruiken.
33. Als **analist**, wil ik een **tooltip** dat MTTF-multiplier vooral **PBS-defaults** beïnvloedt, niet retroactief alle FM-MTTF’s, zodat verwachtingen kloppen.
34. Als **maintainer**, wil ik dat **`effective_sigma`** de config-fractie gebruikt i.p.v. hardcoded 0,15, zodat het dialoogveld niet misleidend is.
35. Als **analist**, wil ik na wijziging sigma-default **herbereken vereist**, zodat aging-resultaten de nieuwe σ volgen.

### Sectie Monte Carlo (later)

36. Als **analist**, wil ik **monte_carlo_n** en **seed** zien maar **niet bewerken** in v1, zodat ik weet wat later komt zonder een half werkende run.
37. Als **analist**, wil ik een **tooltip** “Monte Carlo nog niet actief in desktop”, zodat disabled velden verklaard zijn.
38. Als **maintainer**, wil ik dat MC-velden **wel** in JSON blijven serialiseren, zodat slice 23 fase F geen migratie hoeft.

### Commit, run en cache

39. Als **analist**, wil ik na OK met **Direct herberekenen** een **incrementele of volledige run** starten volgens bestaand run-beleid, zodat de werkruimte ververst.
40. Als **maintainer**, wil ik **`CACHE_INPUTS_VERSION` bump** bij `effective_sigma`-fix, zodat incrementele cache geen verkeerde FM-resultaten hergebruikt.
41. Als **maintainer**, wil ik dat config-wijzigingen al in **FM-invoerhash** zitten (volledige `config` in hash-slice), zodat affected FM’s correct worden herberekend.
42. Als **maintainer**, wil ik dat bulk-apply aging **FM-hash** van alle aging-FM’s invalideert, zodat alleen die FM’s opnieuw rekenen bij incrementele run.

### Validatie en persistentie

43. Als **analist**, wil ik validator-fouten op **lifecycle ≤ 0**, **monte_carlo_n < 100**, **multiplier ≤ 0**, **sigma_fraction ≤ 0** vóór OK zien, zodat config altijd geldig is.
44. Als **analist**, wil ik **atomisch opslaan** (.rcm.json) bij bekend pad, zodat partial writes worden vermeden (zelfde als FM-editor).
45. Als **maintainer**, wil ik **deserialisatie-backward-compat**: ontbrekende nieuwe velden krijgen veilige defaults, zodat oude fixtures laden.

### UI-kwaliteit

46. Als **analist**, wil ik **conditionele zichtbaarheid** van default β alleen bij Weibull-default, zodat het formulier overzichtelijk blijft.
47. Als **analist**, wil ik **Nederlandse labels** consistent met FM-editor/batch-grid voor aging-distributie, zodat terminologie eenduidig is.
48. Als **power user**, wil ik het dialoog **modaal** houden, zodat ik niet per ongeluk de werkruimte wijzig tijdens instellen.

### Developer ergonomie

49. Als **agent**, wil ik een **deep module** `model_settings_service` met smalle API (load draft, validate, apply aging, commit), zodat UI dun blijft.
50. Als **agent**, wil ik implementatievolgorde **kern → apply → commit → UI**, zodat TDD tracer bullets groen blijven.
51. Als **maintainer**, wil ik **geen tabulaire editing-pipeline voor config in v1**, zodat scope beperkt blijft; directe project-patch via adapter volstaat.

## Implementation Decisions

### Deep modules (test-first op adapter + kern)

| Module | Rol | Interface (conceptueel) |
|--------|-----|-------------------------|
| **Model settings service** | Draft ↔ project, validatie, apply aging, motorrelevante diff | `build_draft(project) -> ModelSettingsDraft`; `validate_draft(draft) -> errors`; `apply_default_aging(project, draft) -> ApplyAgingResult {count, fm_ids}`; `commit_draft(project, draft, *, save_path, rerun) -> CommitResult` |
| **Model settings commit helper** | Atomisch save + stale-run flag + optionele run hook | Parity met `FmEditCommitService`-patroon: validate → materialiseer project → `save_project_atomically` → optioneel `run_incremental_analysis` |
| **Domain model (`RCMProject`, `RCMConfig`)** | Persistentie + defaults | Nieuwe velden; `effective_sigma` koppeling |
| **Validators (`RCMConfig`)** | Hard errors vóór run | Uitbreiding voor `default_aging_distribution`, `default_beta_jaar` |
| **Cache digest policy** | Metadata uitsluiten indien nodig | `projectnaam`/`modelleur` buiten motor-impact; config blijft in FM-hash |
| **ModelSettingsDialog (view)** | Qt-formulier, secties, Apply-knop, OK/Annuleren | Leest/schrijft alleen via adapter; geen directe `rcm_core`-imports |
| **Results workspace toolbar** | Entrypoint + dirty-grid guard | Hergebruik `resolve_grid_dirty_before_editor` |

### Schema-wijzigingen

**RCMProject — top-level (metadata, geen motor-impact):**

```
projectnaam: str = ""
modelleur: str = ""
```

**RCMConfig — nieuwe defaults:**

```
default_aging_distribution: "normal" | "truncated_normal_0" | "weibull_2p"   # default "normal"
default_beta_jaar: float = 0.0   # verplicht > 0 wanneer default_aging_distribution == "weibull_2p"
```

**Migratieregel:** ontbrekende velden ⇒ defaults hierboven. Bestaande `lifecycle_years`, `modeljaar`, `default_mttf_multiplier`, `default_sigma_fraction`, `monte_carlo_*` ongewijzigd semantisch.

**Faalwijze.effective_sigma:** bij `sigma_jaar == 0` gebruik `project.config.default_sigma_fraction * mttf_jaar` (niet hardcoded 0,15). Vereist project-context in aanroepers die effective_sigma nodig hebben (property → methode of expliciete config-parameter).

**Digest/cache:**

- `projectnaam` / `modelleur`: **niet** opnemen in `compute_global_digest` / FM-hash (metadata-only). Implementatie: exclude keys in digest builder **of** houd ze buiten `to_dict()` motor-pad — kies één consistente aanpak en documenteer in issue.
- **`CACHE_INPUTS_VERSION` bump** verplicht wegens `effective_sigma`-gedragswijziging.

### Apply aging — semantiek

- Alleen faalwijzen met `failure_type == aging`.
- Zet `aging_distribution` = draft.default_aging_distribution; bij Weibull ook `beta_jaar` = draft.default_beta_jaar.
- Teller + bevestigingsdialoog vóór mutatie.
- Geen automatische apply bij OK — expliciete knop only.
- Random-FM’s: ongemoeid.

### OK / commit — semantiek

- Valideer draft (config + metadata + eventuele pending FM-wijzigingen na Apply).
- Werk in-memory project / `ProjectSession` bij.
- **Atomisch opslaan** wanneer `project_path` bekend (`save_to_disk=True` patroon FM-editor).
- Bepaal `requires_rerun` wanneer motorrelevante velden wijzigden (config, apply aging, niet metadata-only).
- Checkbox **Direct herberekenen**: alleen enabled als `requires_rerun`; default **uit**; bij aan: incrementele run (`full_recompute=False`) tenzij lifecycle/modeljaar globale digest invalidateert — volg bestaand run-beleid werkruimte.
- **Dirty faalwijzen-grid guard** vóór openen dialoog (hergebruik bestaande guard).

### UI — secties en gedrag

- **Knop:** alleen resultatenwerkruimte-toolbar (naast batch-faalwijzen / herbereken).
- **Secties/tabs:** Project | Horizon & tijd | Veroudering defaults | Standaard faalparameters | Monte Carlo (disabled).
- **Read-only:** “Bucket-interval: 1 kalenderjaar” (afgeleid; geen config-veld).
- **Monte Carlo:** velden zichtbaar, disabled, tooltip.
- **Titel:** `Modelinstellingen — {projectnaam or filename}`.

### Import — projectnaam voorinvullen

- Bij Isograph-import: als `projectnaam` leeg, vul vanuit `Description` of bestandsnaam (bestaande metadata in `import_settings["isograph_project"]` als bron).
- `modelleur`: niet automatisch invullen in v1.

### Architectuurprincipes (AGENTS.md)

- UI/kern-decoupling: views via adapter; geen directe `rcm_core.*` in views behalve typing-only.
- Geen tabulaire editing-pipeline voor `config` in v1.
- TDD op adapterlaag (`model_settings_service`); pure UI niet test-gestuurd.
- Parity-test persistence bij wijziging `RCMProject.to_dict()` vorm.

### Prototype — draft shape (beslissingsrijk)

```python
@dataclass
class ModelSettingsDraft:
    projectnaam: str
    modelleur: str
    lifecycle_years: float
    modeljaar: int
    default_aging_distribution: str
    default_beta_jaar: float
    default_mttf_multiplier: float
    default_sigma_fraction: float
    # monte_carlo_* read-only mirror for display
```

## Testing Decisions

### Wat maakt een goede test

- Test **extern gedrag**: serialisatie roundtrip, validator blok/allow, apply-aging count + FM-velden, effective_sigma na config-wijziging, commit + save conflict, requires_rerun flag — niet interne Qt-widgetstructuur.
- **Metadata-only commit** mag geen rerun vereisen; **lifecycle-wijziging** wel.
- **Baselines:** herbereken verwachte metrics waar `effective_sigma`-fix Haarlem-FM’s met `sigma=0` raakt.

### Te testen modules

| Module | Testtype | Prior art |
|--------|----------|-----------|
| RCMProject/RCMConfig serialisatie + defaults | Unit | `tests/test_persistence.py` |
| Validators config (aging default, β) | Unit | `rcm_core/validators.py` CFG_* tests |
| `effective_sigma` + config fraction | Unit | FM model tests, slice 51 aging |
| `apply_default_aging_to_fms` | Unit | bulk grid tests, FM edit scope |
| `model_settings_service` commit/save/rerun flag | Adapter unit | `tests/test_desktop_fm_edit_services.py`, `fm_edit_commit_service` |
| Cache digest excludes metadata | Unit | `tests/test_cache*.py` |
| Dirty-grid guard vóór open | pytest-qt smoke | `grid_dirty_guard`, FM editor open tests |
| Dialog smoke (open/OK/cancel) | pytest-qt adapter/view | workspace FM editor tests |

### Baseline-beleid

- Verwacht **shift** in run-metrics voor fixtures met veel `sigma_jaar=0` FM’s na `effective_sigma`-fix — documenteer delta en update asserts gericht (niet blind hele portfolio).
- Metadata-velden: geen baseline-wijziging.

## Out of Scope

- **`failure_type` projectbreed** instellen (blijft FM-editor + faalwijzen batch-grid).
- **Monte Carlo-run** in desktop (slice 23 fase F); velden alleen tonen/disabled.
- **Tabulaire editing-pipeline / ENTITY_SCHEMAS voor config** in v1.
- **Modelinstellingen in ValidateWindow** of hoofdmenu-only entrypoint.
- **Automatische apply aging bij OK** zonder expliciete knop.
- **Retroactief alle FM-MTTF’s** bij wijziging `default_mttf_multiplier` (alleen PBS-defaults; tooltip).
- **Aparte config-veld voor bucket-interval** (blijft afgeleid 1 jaar).
- **Modelleur auto-import** uit Isograph.
- **Rapportage-export** die projectnaam/modelleur gebruikt (alleen data voorbereiden).
- **Bulk “reset naar defaults”** voor sigma/MTTF per FM.
- **Projectdefaults voor nieuwe FM’s** bij aanmaken (defaults in config zijn referentie + apply-knop, geen factory-hook).

## Further Notes

### Voorgestelde implementatievolgorde (tracer bullets)

1. **Kern:** `RCMProject` metadata + `RCMConfig` defaults + validators + `effective_sigma`-koppeling + `CACHE_INPUTS_VERSION` bump + persistence tests.
2. **Apply aging:** `apply_default_aging_to_fms()` + count/bevestiging in service.
3. **Commit:** save atomically + `requires_rerun` + optionele rerun hook (adapter).
4. **UI:** `ModelSettingsDialog` + toolbar-knop + dirty-grid guard + pytest-qt smoke.

### Deep modules — verwachting implementatie

De PRD gaat uit van **test-first** op:

- **Model settings service** (adapter, Qt-vrij) — primair
- **Kern:** validators + `effective_sigma` + serialisatie — primair
- **ModelSettingsDialog** (view) — smoke only via pytest-qt

### Bekende risico’s

- **Apply aging overschrijft per-FM uitzonderingen** — bewust; bevestiging + teller mitigeren.
- **`effective_sigma`-fix** kan brede baseline-impact — gerichte assert-updates.
- **Digest exclude metadata:** implementatiekeuze (exclude in digest vs. apart metadata-blok) moet in issue 01 vastliggen om dubbele waarheid te vermijden.
- **`effective_sigma` als property:** callers moeten config doorgeven — refactor-scope beperken tot aanroepers die motor/validatie raken.

### Verwante slices

- **Slice 51:** `aging_distribution` per FM — defaults in slice 52 bouwen daarop.
- **Slice 44/46:** FM-editor commit + dirty-grid guard — patronen hergebruiken.
- **Slice 23:** resultatenwerkruimte toolbar + toekomst MC.
- **Slice 35:** Isograph-import metadata voor projectnaam-voorinvulling.
