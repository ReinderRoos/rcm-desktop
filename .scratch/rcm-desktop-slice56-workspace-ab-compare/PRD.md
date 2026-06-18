# PRD — RCM2 desktop slice 56 (resultatenwerkruimte A/B-scenariovergelijking)

**Status:** done  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** Feature (adapter + view; geen schema-drift op `RCMProject`)  
**Parent:** grill-me sessie scenariovergelijking (2026-06-02); bouwt voort op slice 23 (werkruimte), slice 28/29/30 (planning-overlay + what-if), slice 33 (Top10-modi)  
**Supersedes (gedeelte):** ADR-0006 — workspace krijgt expliciet goedgekeurd A/B-vergelijkingsmodel; legacy `CompareRunner` blijft ValidateWindow-only  
**Datum:** 2026-06-02

## Problem Statement

Reliability-analisten willen **twee analyse-uitkomsten naast elkaar** vergelijken — bijvoorbeeld een **referentie-run** (baseline, CM-beleid of PM-scenario) tegen een **variant-run** waarbij PM-taken zijn uitgezet, verplaatst (meekoppelen) of REV is uitgesteld — **zonder** terug te vallen op het verouderde ValidateWindow CM/PM-vergelijkingspaneel.

De resultatenwerkruimte ondersteunt sinds slice 29 **één `last_run` plus what-if overlay**. Dat werkt voor iteratief experimenteren, maar niet voor **stabiele A/B-vergelijking**: de analist kan niet tegelijk een bevroren referentie en een bevroren variant naast elkaar houden terwijl hij PBS-scope en taaktype-filters (CM/REV/IN/SVO/TST) **één keer** bedient voor beide weergaven.

In **Top 10** en **Tijdsplot** ontbreekt daarom:

- een workflow om **twee motorruns** expliciet vast te leggen (A = referentie, B = variant);
- split-weergave (Top10 naast elkaar, Tijdsplot gestapeld) die **beide runs** bijwerkt bij PBS-selectie en gedeelde filters;
- duidelijkheid over **welke overlay/scenario-configuratie** bij welke run hoort, zonder stille herberekening achteraf.

ADR-0006 verbood scenario/compare-UI in de werkruimte ten gunste van single-run what-if. Dit productbesluit **herintroduceert vergelijking** met een **nieuw, generiek A/B-model** — niet de oude vaste CM/PM-scenario-slots.

## Solution

Introduceer **A/B-vergelijking in de resultatenwerkruimte**:

1. **Twee bevroren slot-snapshots (A/B)** — elke slot-run slaat `RunResult`, presentation-cache, scenario-keuze (Project / CM / PM) en overlay op **run-moment** op.
2. **Gedeeld pre-run config-paneel** — analist stelt scenario + overlay/meekoppel in vóór **Run → A** of **Run → B**; geen verplichte dubbele run (seeding via “Zet huidige run als A/B” of cache-hydratie na validate).
3. **Opt-in toggle “Vergelijk A ↔ B”** — uit = huidige single-run UX op `last_run`; aan = split in Top10 (twee kolommen) en Tijdsplot (gestapeld, gesynchroniseerd kalenderjaar + gedeelde Y-as-max).
4. **Gedeelde navigatie** — één PBS-selectie, één taaktype-filterset (CM/REV/IN/SVO/TST/WET), gedeelde Top10-sub-toggles; her-renderen beide slots zonder motorrun.
5. **Lifecycle gelijk aan `last_run`** — slots hard wissen bij padwijziging, validate/import-success en leeg project; sessie-only (geen persistente A/B op schijf in v1).
6. **Nieuwe ADR** — workspace A/B compare expliciet toegestaan; legacy compare-stack blijft ValidateWindow-only.

De huidige **Analyse**-knop wordt vervangen door **Run → A** en **Run → B**.

## User Stories

### Workflow en mentaal model

1. Als reliability-analist wil ik een **referentie-run** (A) kunnen draaien in baseline, CM- of PM-configuratie, zodat ik een vast uitgangspunt heb voor vergelijking.
2. Als reliability-analist wil ik daarna een **variant-run** (B) kunnen draaien met dezelfde project-JSON maar andere overlay/meekoppel-instellingen, zodat ik het effect van PM-wijzigingen zie.
3. Als reliability-analist wil ik **niet verplicht** beide runs achter elkaar te draaien, zodat ik een reeds gedraaide referentie kan hergebruiken.
4. Als reliability-analist wil ik **“Zet huidige run als A”** / **“… als B”** kunnen gebruiken, zodat cache-hydratie na validate voldoende is voor de referentie-slot.
5. Als reliability-analist wil ik **Run → A** en **Run → B** als expliciete acties, zodat ik controle heb over welke slot wordt overschreven.
6. Als reliability-analist wil ik dat **`last_run`** de meest recente slot-run volgt, zodat single-run modus voorspelbaar blijft wanneer vergelijk-toggle uit staat.
7. Als trainer wil ik begrijpen dat **overlay-wijzigingen na een run** de gevulde slot **niet** stilletjes wijzigen, zodat A/B betrouwbaar blijft tot expliciete re-run.

### Pre-run configuratie

8. Als analist wil ik vóór elke run **Scenario: Project / CM / PM** kunnen kiezen, zodat ik CM- of PM-beleid kan vergelijken zonder ValidateWindow.
9. Als analist wil ik **planning-overlay en meekoppel** in hetzelfde config-paneel kunnen instellen, zodat variant B meekoppel- en REV-uitstel-effecten materialiseert.
10. Als analist wil ik dat scenario + overlay bij Run → A/B **bevroren** worden in het slot, zodat ik later nog kan zien welke configuratie bij welke curve hoort.
11. Als analist wil ik een **leesbaar slot-label** (bijv. “A — PM-baseline”, “B — 3 REV passief + meekoppel”), zodat split-panelen self-explanatory zijn.

### Vergelijk-toggle en layout

12. Als analist wil ik een toggle **“Vergelijk A ↔ B”** (standaard uit), zodat single-run de norm blijft en vergelijking opt-in is.
13. Als analist wil ik bij toggle **aan** in **Top 10** twee volledige kolommen (A | B) met elk grafiek + tabel, zodat ik beide top-10-lijsten direct kan scannen.
14. Als analist wil ik bij toggle **aan** in **Tijdsplot** twee stacked-bar charts **gestapeld**, zodat ik kalenderjaarkosten van beide runs zie.
15. Als analist wil ik **gesynchroniseerd kalenderjaar** over beide Tijdsplot-panelen, zodat jaarklik in boven- of onderste chart hetzelfde jaar selecteert.
16. Als analist wil ik een **gedeelde Y-as-max** over beide Tijdsplot-panelen, zodat visuele hoogte eerlijk vergelijkt.
17. Als analist wil ik bij een **leeg slot** een placeholder (“Run → A” / “Run → B”), zodat ik kan starten met alleen referentie A.
18. Als analist wil ik knop **“Wis vergelijking”**, zodat ik A/B reset zonder project te wisselen.

### Gedeelde navigatie en filters

19. Als analist wil ik **één PBS-selectie** in de sidebar, zodat beide versies dezelfde scope tonen.
20. Als analist wil ik **CM/REV/IN/SVO/TST/WET-filters één keer** te bedienen, zodat filterwijziging beide slots tegelijk her-rendert.
21. Als analist wil ik **Top10-sub-toggles** (bron, metric, horizon, NB-weergave) gedeeld, zodat metric-wissel beide kolommen bijwerkt.
22. Als analist wil ik dat PBS- of filterwijziging **geen motorrun** triggert, zodat vergelijking snel responsief blijft.

### Modi en scope

23. Als analist wil ik vergelijking in **Top 10** en **Tijdsplot**, zodat mijn beschreven workflow gedekt is.
24. Als analist wil ik dat **FM-detail** single-run blijft in v1, zodat complexiteit beperkt blijft.
25. Als analist wil ik dat vergelijk-toggle **uit** in FM-detail geen split toont, zodat gedrag consistent is.

### Lifecycle, cache en invalidatie

26. Als analist wil ik dat A/B-slots **gewist** worden bij **projectpad-wijziging**, zodat ik geen runs van een ander bestand vergelijk.
27. Als analist wil ik dat A/B-slots **gewist** worden na **succesvolle validate/import**, zodat vergelijking op actuele project-inhoud baseert.
28. Als analist wil ik dat slots **sessie-only** zijn (v1), zodat invalidatie eenvoudig blijft.
29. Als analist wil ik na validate **cache-hydratie** kunnen gebruiken als seed voor slot A, zodat ik niet opnieuw hoef te draaien.

### Fouten en randgevallen

30. Als analist wil ik bij **Run → B mislukt** dat slot **A ongemoeid** blijft, zodat referentie niet verloren gaat.
31. Als analist wil ik bij run-fout een **foutdialoog** en placeholder/banner in het betreffende paneel, zodat ik kan retryen.
32. Als analist wil ik dat een **vorige B-run** behouden blijft als nieuwe Run → B faalt, zodat ik niet alles kwijtraak.

### Architectuur en onderhoud

33. Als ontwikkelaar wil ik een **nieuwe ADR** die workspace A/B compare toestaat, zodat ADR-0006 niet impliciet wordt geschonden.
34. Als ontwikkelaar wil ik dat **legacy CompareRunner** en CM/PM-KPI’s **ValidateWindow-only** blijven, zodat geen dubbele compare-paden ontstaan.
35. Als ontwikkelaar wil ik **`CompareSlotState` (A/B)** i.p.v. oude `ScenarioSlotState` (cm/pm keys) hergebruiken, zodat het model generiek is.
36. Als ontwikkelaar wil ik **render-index slot-keys `SLOT_A` / `SLOT_B`**, zodat presentatie-cache per slot memoized blijft.
37. Als ontwikkelaar wil ik dat LCC per slot de **bevroren overlay** uit het slot gebruikt, niet live workspace-overlay, zodat vergelijking correct is.
38. Als ontwikkelaar wil ik **Qt-vrije adapter-services** voor slot- en split-logica, zodat unit-tests klein blijven.
39. Als ontwikkelaar wil ik **`compute_split_layout`** opnieuw relevant maken voor A/B (vertical = Tijdsplot, horizontal = Top10), zodat legacy split-semantiek hergebruikt wordt.

### Toegankelijkheid en copy

40. Als gebruiker wil ik **Nederlandse labels en tooltips** via message constants, zodat copy consistent is met de rest van de werkruimte.
41. Als gebruiker wil ik tooltips die uitleggen dat **vergelijking opt-in** is en **geen dubbele run verplicht**, zodat onboarding eenvoudig blijft.

## Implementation Decisions

### ADR en scope-afbakening

- **Nieuwe ADR (voorstel ADR-0007):** workspace **A/B compare** is toegestaan in resultatenwerkruimte; `CompareRunner`, `scenario_compare_service` KPI-flow en CM/PM-dubbelrun-UI blijven **legacy ValidateWindow-only** (ADR-0006 blijft geldig voor die stack).
- **Niet** de oude `ScenarioSlotState` cm/pm-keys reanimeren; nieuw generiek **A/B-model**.
- **v1 modi:** Top10 + Tijdsplot only; FM-detail blijft single-run.

### Diepe modules en interfaces

- **CompareSlotSnapshot (immutable)**  
  Bevat per slot: `RunResult`, optionele `PresentationProjectTotal`, `scenario_key` (`None` = project-as-loaded, `"cm"`, `"pm"`), bevroren `PlanningOverlayState`, gegenereerd `label` (mensleesbaar).

- **CompareSlotState (Qt-vrij)**  
  In-memory A/B-opslag; API: `get(slot)`, `put(slot, snapshot)`, `clear_all()`, `clear(slot)`, `seed_from_last_run(slot, last_run, …)`, `has(slot)`, `both_filled()`. Subscribes/listeners analoog aan workspace-state.

- **CompareRunConfig**  
  Gedeelde pre-run configuratie: `scenario_key`, `planning_overlay`, eventueel `force_recompute`. Wordt bij Run → A/B omgezet naar `CompareSlotSnapshot` via motor + presentation-build.

- **CompareRunService**  
  Orchestreert één slot-run: materialiseert project (`build_project_for_scenario` indien CM/PM; `materialize_project_for_overlay` indien overlay actief), roept `run_service.run` aan, bouwt presentation, retourneert snapshot. Geen Qt.

- **CompareSplitLayoutService**  
  Herimplementatie boven bestaande `compute_split_layout`-contract: bij `compare_mode=True` + modus Top10 → `SPLIT_HORIZONTAL` (A links, B rechts); modus Tijdsplot → `SPLIT_VERTICAL` (A boven, B onder); anders `SPLIT_NONE`.

- **CompareViewService**  
  Bouwt `BijdragenCompareView` en `LCCCompareView` uit twee snapshots + gedeelde `WorkspaceStateSnapshot` (scope, filters, metric, calendar year). **Per slot:** eigen run + bevroren overlay; **gedeeld:** scope_id, lcc_filters, contribution_presentation, metric, source, top_n.

- **ComparePresentationPolicy**  
  Bepaalt gedeelde Y-as-max voor Tijdsplot (max over beide bucket-reeksen), gesynchroniseerd kalenderjaar, en invalidatie bij slot-update / project-change.

- **CompareWorkspaceController**  
  Post-run plan: welk slot vullen, `last_run` bijwerken, render-index invalidatie per slot-key, compare-toggle state.

- **CompareRunRunner (Qt)**  
  Extensie of sibling van `RunRunner`: `start_slot(project, path, slot, config)` met background thread; signal `slot_result_ready(slot, snapshot)`.

- **ResultsWorkspaceState uitbreiding**  
  Veld `compare_mode: bool` (default `False`); toggle subscribe → split re-render.

- **View-wijzigingen (ResultsWorkspaceWindow)**  
  - Vervang Analyse-knop door Run → A, Run → B.  
  - Toggle Vergelijk A ↔ B, knoppen Zet als A/B, Wis vergelijking.  
  - Pre-run config: scenario-selector + bestaande overlay/meekoppel UI.  
  - Split-container voor Top10 (2 kolommen) en Tijdsplot (2 charts); placeholders bij leeg slot.  
  - Slot-labels in paneelheaders.

### Slot-snapshot en overlay-semantiek

Bevroren snapshot per slot (prototype type shape uit grill-me):

```python
@dataclass(frozen=True)
class CompareSlotSnapshot:
    run_result: RunResult
    presentation: PresentationProjectTotal | None
    scenario_key: str | None  # None | "cm" | "pm"
    overlay_at_run: PlanningOverlayState
    label: str
```

- **Live workspace `planning_overlay`** beïnvloedt alleen **volgende** Run → A/B, niet reeds gevulde slots.
- LCC/Top10-build per slot gebruikt **`overlay_at_run`** uit snapshot, niet `snapshot.planning_overlay` uit workspace-state.

### Run- en last_run-gedrag

- Run → A/B roept `CompareRunService` aan; bij succes: slot vullen, `last_run` = die run, presentation-cache attach per projectpad.
- Seeding “Zet huidige run als A/B”: snapshot bouwen uit huidige `last_run` + huidige config-metadata (scenario + overlay op seed-moment).
- `last_run` bij toggle **uit**: enkelvoudige weergave zoals nu; bron = meest recente slot-run.

### Invalidatie (gelijk aan last_run)

Hard clear A/B + compare-toggle uit (of placeholders) bij:

- projectpad-wijziging;
- succesvolle validate/import (nieuw project geladen);
- project = None;
- expliciet “Wis vergelijking”.

Sessie-only: geen disk-persistentie van slot-toewijzing in v1.

### Foutafhandeling

- Run-fout op één slot: andere slot ongemoeid; foutdialoog; leeg slot blijft placeholder; bestaande B blijft bij mislukte re-run B.

### Legacy-grenzen

- **Geen** wijzigingen aan ValidateWindow compare-flow behalve eventueel gedeelde run-service hergebruik.
- **Geen** delta-tabel (20 rijen met A/B/delta) in v1.
- **Geen** persistente slot-metadata op schijf in v1.
- **Geen** stale-badges na FM-edit in v1 (hard wissen alleen op validate/padwissel).

### Render-index

- Nieuwe constanten `SLOT_A`, `SLOT_B` naast `SLOT_CURRENT`.
- `on_slot_updated(SLOT_A | SLOT_B)` bij slot-run of seed.
- Compare-views roepen `get_or_build` per slot aan met gedeelde scope/modus-key.

### Scenario-materialisatie

- **Project:** geladen `RCMProject` + overlay-materialisatie indien overlay actief bij run.
- **CM / PM:** `build_project_for_scenario` vóór overlay-materialisatie; scenario-key in snapshot voor cache (`*.rcm.cache.cm.json` / `pm.json` compatibiliteit).

## Testing Decisions

Goede tests valideren **observeerbaar gedrag** via publieke adapter-interfaces, niet implementatiedetails van Qt-widgets.

### Testprincipes

- Test slot-state transities (put, clear, seed, both_filled) zonder Qt.
- Test dat gedeelde PBS/filter-wijziging **twee verschillende** presentation-outputs oplevert zonder tweede motorrun (mock runs).
- Test dat overlay-wijziging in workspace-state **niet** de render van een gevuld slot verandert tot re-run.
- Test invalidatie: padwijziging / validate-success → slots leeg.
- Test split-layout: compare_mode + modus → juiste orientation.
- Test Y-as-max sync en gedeeld kalenderjaar in compare LCC view service.
- Test run-fout op B: A snapshot intact.

### Modules met tests (verplicht)

| Module | Type test |
|--------|-----------|
| `CompareSlotState` | unit |
| `CompareRunService` | unit (mock run) |
| `CompareSplitLayoutService` | unit |
| `CompareViewService` | unit |
| `ComparePresentationPolicy` | unit |
| `CompareWorkspaceController` | unit |
| `ResultsWorkspaceWindow` (smoke) | integratie — toggle, placeholders, geen regressie single-run |

### Prior art

- `tests/test_desktop_scenario_slot_state.py` (legacy slot-patronen)
- `tests/test_desktop_results_workspace_window.py` (modi, Top10 subbar, LCC)
- `tests/test_slice53_issue07_legacy_pr7a.py` (ADR-0006 regressie — uitbreiden met “nieuwe A/B path bestaat, legacy compare niet in workspace window source”)
- `tests/test_desktop_scenario_compare_service.py` (legacy KPI — blijft gescheiden)
- `tests/test_slice28_workspace_smoke.py` / planning-overlay tests

### Regressie-gates

- Legacy ValidateWindow compare-flow blijft groen indien `--legacy-validate` tests bestaan.
- Single-run pad (toggle uit) gedrag ongewijzigd na één Run → A.
- ADR-0006 blijft waar voor legacy; ADR-0007 documenteert workspace-uitzondering.

## Out of Scope

- **FM-detail** split-vergelijking (v1).
- **Delta-tabel** (gecombineerde 20 rijen met A-waarde / B-waarde / Δ) — latere slice.
- **Persistente A/B-slots op schijf** over app-sessies heen (v1 sessie-only).
- **Stale-badges** na FM-edit zonder validate (v1).
- **ValidateWindow** compare-UI wijzigingen of verwijdering.
- **Horizontale KPI-vergelijkingstabel** (legacy scenario_compare_service) in werkruimte.
- **Automatische dubbele run** (CM+PM in één klik) — expliciet afgewezen.
- **Scoped LCC gedrag wijzigen** buiten wat nodig is om PBS-scope in compare consistent te maken met Top10 (indien huidige LCC nog project-totaal tooltip claimt, copy/gedrag alignen is in scope; grote scoped-LCC-feature niet).

## Further Notes

- Deze PRD codificeert de grill-me sessie (2026-06-02) en **herziet gedeeltelijk** het productbesluit uit slice 29 (“geen CM/PM-scenariovergelijking in werkruimte”) ten gunste van **expliciete A/B-slots** — niet terug naar oude cm/pm slot-UI.
- **Relatie slice 29/30:** what-if overlay blijft het mechanisme voor variant-configuratie; vergelijking voegt **tweede bevroren run** toe naast iteratief single-run.
- **Implementatie-volgorde (suggestie):** ADR-0007 → CompareSlotState + CompareRunService → CompareViewService + split layout → RunRunner/slot UI → view split containers → regressie.
- **Risico:** `build_lcc_view` gebruikt vandaag live `planning_overlay`; compare vereist per-slot overlay uit snapshot — centrale fix in CompareViewService / lcc view entry point.
- **Risico:** CM/PM cache-bestanden en scenario-key in snapshot moeten consistent blijven voor hydratie/seeding.
- Uitvoering in kleine issues via `to-issues` skill aanbevolen na PRD-merge.
