# PRD — Strategische roadmap RCM2 desktop (grill juni 2026)

**Status:** done  
**Versie:** 1.0  
**Datum:** 2026-06-13  
**Triage:** `done`  
**Merge:** PR #35 (`feat/workspace-rapportage-slice58`) — 2026-06-13  
**Type:** Meta-roadmap + gefaseerde product- en architectuurslices  
**Parent:** `/grill-with-docs` sessie open taken (2026-06-13); architectuurplan juni 2026; slices 87–94 (werkruimte-stabilisatie)  
**Relatie:** slice 56/60 (A/B-compare), slice 79 (view-registry), slice 50/41 (orchestrator-ontvlechting), epic parity/portfolio/MC (`GRILL_DECISIONS.md`), ADR-0006/0007 (compare), ADR-0014/0015 (input-grid)

> Synthese van **alle principiële grill-besluiten** (2026-06-13). Technische
> en detailbesluiten volgen de aanbevelingen in de sessie; alleen
> product-/principiële keuzes zijn geïnterviewd. Deze PRD is de bron voor
> volgende slices 95+ — geen enkele slice implementeert alles tegelijk.

---

## Problem Statement

De RCM2-desktop is gegroeid van één **resultatenwerkruimte** rond één model naar
Input/Output-views, generiek entiteiten-grid en edit-unificatie (slices 79–94).
Analisten kunnen dagelijks invoeren en resultaten bekijken, maar:

- **Chrome en navigatie** zijn deels nog legacy-`modus`-gedreven; regressies
  (bv. acties op de verkeerde view) blijven mogelijk zolang beleid verspreid zit.
- **Twee entrypoints** (ValidateWindow en resultatenwerkruimte) verwarren en
  kosten dubbel onderhoud.
- De **langere roadmap** (veel modellen, faalwijzen vergelijken, uniformeren,
  Monte Carlo, bibliotheek) heeft geen vastgelegd productkader — agents en
  ontwikkelaars riskeren impliciet de werkruimte tot alles-centrum te maken.

Zonder vastgelegde principes ontstaat architectuurfrictie: verkeerde prioriteit
(MC vóór vergelijken), stille modelwijzigingen bij uniformeren, of compare-UI
die niet aansluit op hoe analisten werken (twee projectbestanden, invoer én
resultaten per faalwijze).

## Solution

Leg **negen principiële besluiten** vast als product- en architectuurkader, en
voer ze uit in **kleine, testbare slices** — geen big-bang:

| Fase | Thema | Grill-besluit(en) |
|------|--------|-------------------|
| **A — Enablers** | Declaratief chrome-beleid in view-registry; derived refresh afronden | #1 |
| **B — Vergelijken v1** | Twee `.rcm.json` ad hoc (A/B), balanced split per FM | #2, #4, #6, #9 |
| **C — Uniformeren v1** | Alleen verschillen tonen + review-only patches + audit trail | #7 |
| **D — Monte Carlo v1** | Optionele run-modus in dezelfde werkruimte | #2, #8 |
| **E — Afsluiting legacy** | ValidateWindow retirement; FM verwijderen | #3, #5 |
| **F — Later** | Portfolio-merge, bibliotheek/templates, canoniek domeinmodel | epic parity/MC |

**Productgravitatie (#2):** de **resultatenwerkruimte** blijft het dagelijkse hart
voor **één geladen model** (invoer + output). Vergelijken, portfolio, Monte Carlo
en bibliotheek zijn **aparte workflows** boven hetzelfde faalwijze-/projectmodel
— geen vervanging van de enkel-model-werkdag.

---

## User Stories

### Productgravitatie en entrypoints

1. As a reliability-analist, I want één dagelijks venster voor invoer en
   resultaten, so that ik niet hoef te kiezen tussen legacy validate en werkruimte.
2. As a reliability-analist, I want mijn normale werkdag te draaien op één
   `.rcm.json` in de resultatenwerkruimte, so that vergelijken en MC opt-in
   blijven en geen verplichting worden.
3. As a trainer, I want duidelijke scheiding tussen “dagelijks enkel model” en
   “speciale workflows” (vergelijken, MC), so that onboarding voorspelbaar blijft.
4. As a product owner, I want expliciet vastgelegd dat portfolio/bibliotheek/MC
   **na** werkruimte-stabilisatie en vergelijken v1 komen, so that scope creep
   wordt tegengegaan.

### Chrome-beleid (view-registry)

5. As a reliability-analist, I want toolbar-acties en filters alleen op views
   waar ze semantisch horen, so that ik geen output-chrome boven invoergrids zie.
6. As a reliability-analist, I want “Nieuwe faalwijze” alleen op Input/Faalwijzen,
   so that resultaten-views read-only blijven qua modelstructuur.
7. As a developer, I want chrome-capabilities declarative per `view_id`, so that
   nieuwe views (LTAP, extra input-views) geen ad hoc orchestrator-functies
   vereisen.
8. As a developer, I want the orchestrator to **interpreteren** van registry-
   metadata, not per-view imperatieve planners uitbreiden, so that regressies
   traceerbaar zijn tot één matrix.

### ValidateWindow retirement

9. As a reliability-analist, I want import en validatie via bestaande wizard en
   werkruimte-menus, so that ValidateWindow niet meer nodig is voor dagelijks werk.
10. As a developer, I want een gefaseerd retirement-pad (feature-parity eerst,
    daarna deprecate), so that `--legacy-validate` tijdelijk veilig blijft.
11. As a developer, I want ADR-0006 legacy compare-stack gescheiden te houden
    van workspace compare (ADR-0007), so that geen dubbele compare-paden ontstaan.

### Modelvergelijking (prioriteit na stabilisatie)

12. As a reliability-analist, I want twee willekeurige projectbestanden (baseline
    A, scenario B) naast elkaar te laden, so that ik geen portfolio-merge nodig
    heb voor een snelle vergelijking.
13. As a reliability-analist, I want per faalwijze **invoer én resultaten**
    even zichtbaar in een balanced split, so that ik zowel keuzes als effect
    kan beoordelen zonder view-wissels.
14. As a reliability-analist, I want duidelijk te zien **welke FM's alleen in A,
    alleen in B, of in beide** zitten, so that structurele vs parameterverschillen
    snel zichtbaar zijn.
15. As a reliability-analist, I want parameterverschillen (MTTF, faaltype,
    aging, PM-koppeling) per FM gemarkeerd, so that modelleerkeuzes snel
    zichtbaar worden.
16. As a reliability-analist, I want resultaatverschillen (kosten, NB, bijdragen)
    naast invoerverschillen per FM, so that afgeleide effecten de invoer bevestigen.
17. As a reliability-analist, I want mapping/terminologieverschillen (zelfde FM,
    andere namen) herkenbaar gescheiden van echte parameterverschillen, so that
    ik niet verkeerde conclusies trek.
18. As a reliability-analist, I want vergelijking te bouwen op bestaande A/B-run-
    slots waar mogelijk, so that ik referentie en variant kan bevriezen zonder
    dubbele run-flows.
19. As a developer, I want compare-logica Qt-vrij in adapter use-cases, so that
    FM-diff en presentatie unit-testbaar blijven.

### Uniformeren

20. As a reliability-analist, I want voorgestelde uniformeringen altijd expliciet
    te beoordelen vóór toepassing, so that geen stille modelcorruptie optreedt.
21. As a reliability-analist, I want een **uniformeringsvoorstel** per verschil
    met duidelijke bron (A→B of B→A), so that ik weet wat er zou veranderen.
22. As a reliability-analist, I want na toepassing een audit trail en rollback,
    so that ik veilig kan experimenteren met harmonisatie.
23. As a product owner, I want **geen automatische merge** op lage drempel in v1,
    so that vertrouwen in het hulpmiddel behouden blijft.
24. As a developer, I want uniformeren als `DifferenceSet → NormalizationProposal
    → UserReview → Patch → AuditTrail`, not directe mutatie op bronmodel, so that
    de pipeline testbaar en omkeerbaar is.

### Monte Carlo

25. As a reliability-analist, I want Monte Carlo als **optionele run-modus** naast
    de analytische run in dezelfde werkruimte, so that ik niet van context hoef
    te wisselen.
26. As a reliability-analist, I want voortgang en reproduceerbare seed zichtbaar,
    so that lange MC-runs beheersbaar zijn.
27. As a developer, I want MC job-orchestratie los van UI-refresh (filters,
    navigatie), so that een filterwijziging geen MC herstart triggert.
28. As a developer, I want MC-resultaten in een aparte result store naast
    analytische `RunResult`, so that presentatie beide modi kan tonen zonder
    cache-conflict (epic GRILL_DECISIONS §3).

### Faalwijze verwijderen

29. As a reliability-analist, I want een faalwijze te kunnen verwijderen vanuit
    Input/Faalwijzen, so that ik dubbele of foutieve FM's kan opruimen.
30. As a reliability-analist, I want een bevestigingsdialoog met waarschuwing
    bij gekoppelde PM-taken, effecten of taakgroepen, so that ik cascade-effect
    begrijp vóór verwijderen.
31. As a developer, I want verwijderen via de tabulaire editing-pipeline met
    validate/materialize, so that run en save consistent blijven.

### Architectuur (use-case-gedreven richting)

32. As a developer, I want nieuwe capabilities als **application use-cases**
    boven `RCMProject`, not as orchestrator-uitbreidingen in het venster, so that
    multi-model en MC schaalbaar blijven.
33. As a developer, I want compare/uniform/MC UI te voeden via view-models/
    presenters, so that views geen `rcm_core` runtime-imports nodig hebben.
34. As a developer, I want incrementele extractie uit `ResultsWorkspaceWindow`
    (slice 41-ratchet), so that het god-window niet verder groeit.

### Afsluiting en kwaliteit

35. As a developer, I want elke roadmap-fase afsluitbaar met gerichte pytest-
    subsets, so that CI betrouwbaar blijft zonder volledige GUI-suite per commit.
36. As a product owner, I want HILT-handchecks (visuele QA, Haarlem meekoppel,
    round-trip export) expliciet vóór merge van grote compare/MC slices, so that
    regressies vroeg worden gevangen.

---

## Implementation Decisions

### Vastgelegde principiële besluiten (grill 2026-06-13)

| # | Onderwerp | Besluit |
|---|-----------|---------|
| 1 | **Chrome-beleid** | Declaratief in **view-registry**; orchestrator interpreteert |
| 2 | **Productgravitatie** | Werkruimte = dagelijks hart **één model**; compare/MC/portfolio later |
| 3 | **ValidateWindow** | Op termijn **weg**; resultatenwerkruimte enige dagelijkse venster |
| 4 | **Prioriteit** | Eerst **vergelijken**, daarna **Monte Carlo** |
| 5 | **FM verwijderen** | Toegestaan vanuit Input/Faalwijzen; bevestiging + koppeling-waarschuwing |
| 6 | **Vergelijk-focus** | **Balanced**: invoerparameters én resultaten per FM even zichtbaar |
| 7 | **Uniformeren** | **Geen auto-merge**; review + audit trail + rollback |
| 8 | **Monte Carlo** | Optionele **run-modus** in dezelfde werkruimte |
| 9 | **Start vergelijking** | **Twee ad hoc projectbestanden** (A/B); geen portfolio vereist |

### Fase A — Chrome-beleid in view-registry (near-term slice)

- Breid `WorkspaceViewEntry` uit met een **chrome-profiel** (werknaam
  `WorkspaceChromeProfile` of equivalent): declarative flags/capabilities
  zoals `allows_new_fm`, `shows_nb_effect_filter`, `shows_metric_combo`,
  `shows_batch_faalwijzen`, `shows_column_crop`, `toolbar_family`
  (`none` | `top10` | `lcc` | `fm` | `input_grid`).
- **ResultsWorkspaceOrchestrator** leest registry + `active_view_id` +
  `workspace_side`; geen nieuwe `_plan_*_chrome` per view tenzij uitzondering
  gedocumenteerd.
- Legacy `modus` blijft **derived** uit `active_view_id` tot volledige
  afbouw; geen nieuwe features mogen alleen op `modus` leunen.
- Migreer bestaande slice 93-gedrag (new FM op input.faalwijzen only) naar
  registry-metadata.

### Fase B — Modelvergelijking v1 (volgende grote productslice)

**Entry:** analist kiest project A en project B (twee `.rcm.json`-paden of
“open second model”); geen portfolio-merge vereist.

**Canoniek compare-pad:**

```text
LoadModel(A) + LoadModel(B)
    → AlignFailureModes (fm_id / fingerprint / mapping rules)
    → DifferenceSet (inhoud | terminologie | structuur | parameterisatie)
    → ComparePresentation (balanced split per FM)
```

- **Balanced split per FM:** UI toont gekoppelde FM-paren met invoerdiff
  (schema-gedreven velden uit editing registry) en resultaatdiff (na run op
  beide modellen, of cache-hydrate) in één scherm — geen aparte “alleen
  params”-modus als default.
- **A/B-run-seam:** hergebruik `CompareSlotState` / workspace A/B (ADR-0007)
  waar slots al bestaan; extend voor **twee projecten** i.p.v. alleen twee
  runs op één project.
- **Vergelijkingswerkruimte:** aparte workflow (wizard of modus), niet de
  dagelijkse enkel-model navigatie vervangen; kan de bestaande werkruimte-
  shell hergebruiken met `CompareSession` state.
- v1 **geen** patch/uniformeren — alleen detecteren en visualiseren (uniformeren
  is fase C).

Type shape (prototype uit grill/architectuurplan):

```python
@dataclass(frozen=True)
class FailureModePair:
    fm_id_a: str | None
    fm_id_b: str | None
    match_kind: str  # "id" | "fingerprint" | "manual" | "unmatched_a" | "unmatched_b"

@dataclass(frozen=True)
class FailureModeDifference:
    pair: FailureModePair
    field_diffs: tuple[FieldDiff, ...]  # input schema fields
    result_diffs: tuple[ResultDiff, ...]  # post-run metrics
    difference_class: str  # "inhoud" | "terminologie" | "structuur" | "parameterisatie"
```

### Fase C — Uniformeren v1

- Pipeline: `DifferenceSet → NormalizationProposal → UserReview → Patch →
  AuditTrail`; **geen** automatische toepassing op lage drempel.
- Patches werken op **doelmodel** expliciet gekozen door analist; bronmodel
  read-only tijdens review.
- Rollback = vorige project-snapshot of patch-undo stack (exact mechanisme
  in slice-PRD; moet audit trail bevatten).
- Terminologie: **uniformeringsvoorstel** in CONTEXT.md (glossary-update bij
  implementatie).

### Fase D — Monte Carlo v1

- **Run-modus** enum op sessie: `analytical` | `monte_carlo`; default
  analytisch (epic GRILL_DECISIONS §3).
- Job-based: `SimulationRequest → SimulationJob → SimulationEngine →
  ResultStore → Presentation`; **niet** in `_on_state_*` refresh-flow.
- UI: voortgang, seed, annuleren; resultaten in bekende output-views waar
  zinvol (FM-resultaten, Top 10 bandbreedtes — detail in MC-slice-PRD).
- `FMMCResult` naast `FMResult`; aparte cache-namespace.

### Fase E — ValidateWindow retirement + FM delete

- **ValidateWindow retirement (gefaseerd):**
  1. Feature-parity checklist (invoer, batch grid, run, rapportage).
  2. `--legacy-validate` blijft voor regressie tot parity bewezen.
  3. ADR voor retirement (hard to reverse) vóór verwijderen uit default startup.
- **FM delete:** actie op Input/Faalwijzen; confirmatie met telling gekoppelde
  entiteiten; implementatie via editing-pipeline `apply_rows` / materialize;
  geen directe `RCMProject`-mutatie buiten pipeline.

### Technische richtlijnen (agent-aanbevelingen, geen grill)

- **Derived refresh:** pure `plan_*_refresh` planners + dunne bindings;
  KPI/PBS-tree volgen slice 92/94-patroon.
- **Slice 41:** incrementele extractie; ratchet `results_workspace_window.py`
  strikt handhaven.
- **Views:** alleen via adapter; `view_core_facade` uitbreiden waar nodig.
- **Scrub-list:** geen `ltap_light`, geen Streamlit-port; Monte Carlo wel
  toegestaan per roadmap maar adapter-only job-pad.

### ADR-kandidaten (bij implementatie van betreffende fase)

| ADR-onderwerp | Wanneer | Criteria |
|---------------|---------|----------|
| ValidateWindow retirement | Fase E start | Hard to reverse, surprising, trade-off |
| Vergelijkingsbeleid (twee bestanden, balanced, geen auto-uniform) | Fase B start | Idem |
| Uniformerings-pipeline | Fase C start | Idem |
| MC run-modus in werkruimte | Fase D start | Idem |

---

## Testing Decisions

Goede tests toetsen **observeerbaar gedrag** via publieke adapter- en
kern-interfaces; geen widget-internals. Prefer **hoogste seam** per fase.

### Fase A — Chrome registry

| Seam | Wat |
|------|-----|
| View-registry + chrome-profiel metadata | Gegeven `view_id`, verwachte capability-flags |
| ResultsWorkspaceOrchestrator | `plan_ui_sync` / toolbar-plannen matchen registry voor elke view |
| Regressie slice 93 | `new_fm_visible` false op output.fm_results, true op input.faalwijzen |

Prior art: `tests/test_slice79_*`, `tests/test_slice91_toolbar_input_side.py`,
`tests/test_slice93_view_aware_input_chrome.py`, `tests/test_results_workspace_orchestrator.py`.

### Fase B — Modelvergelijking v1

| Seam | Wat |
|------|-----|
| `AlignFailureModes` / compare use-case (Qt-vrij) | Paar-vorming, unmatched A/B, difference_class |
| Field diff over editing schema | MTTF/type wijkt → `FieldDiff` |
| Compare presentation service (Qt-vrij) | Balanced DTO bevat zowel field_diffs als result_diffs per paar |
| CompareSession / dual-project load | Twee projecten laden zonder portfolio |
| Workspace compare + dual project (integratie smoke) | Open A+B, minimaal één FM-paar zichtbaar |

Prior art: `tests/test_desktop_scenario_slot_state.py`, slice 56/60 compare tests,
`tests/test_editing_schemas_parity.py`.

### Fase C — Uniformeren

| Seam | Wat |
|------|-----|
| NormalizationProposal builder | Geen patch zonder expliciet `approved=True` |
| Patch apply + AuditTrail | Patch reversible; audit entry aanwezig |
| Materialize guard | Geen stille apply op validate/run |

### Fase D — Monte Carlo

| Seam | Wat |
|------|-----|
| SimulationJob lifecycle | seed, status, cancel |
| ResultStore | analytisch vs MC gescheiden |
| Run-modus switch | MC start triggert **geen** derived refresh storm |

Prior art: epic GRILL_DECISIONS §3; `tests/test_validators.py` waar MC parity.

### Fase E — FM delete

| Seam | Wat |
|------|-----|
| Delete use-case via EntityEditService | FM verdwijnt; gekoppelde waarschuwing in UI-model |
| validate_project na delete | Geen orphan FK errors |

### Algemene principes

- Test **gedrag**, niet planner-functienamen.
- Geen volledige test-suite als CI-gate per slice; wel slice-specifieke subset
  in PRD/issues documenteren.
- GUI-smoke alleen waar geen lagere seam het contract dekt (HILT rest).

---

## Out of Scope

**Van deze roadmap-PRD als geheel (komen in latere PRD's per fase):**

- Volledige implementatie van fase B–E in één slice.
- Portfolio-merge als **vereiste** voor vergelijken (besluit #9: ad hoc twee
  bestanden eerst).
- Automatische uniformering op lage drempel (besluit #7).
- Monte Carlo vóór vergelijken v1 af (besluit #4).
- Canoniek domeinmodel met `ModelVersion`, `LibraryModel` als verplichte
  tussenlaag vóór compare v1 — `RCMProject` blijft bron tot expliciet ADR.
- ValidateWindow verwijderen **zonder** parity-checklist (besluit #3 is
  eindbeeld, niet immediate delete).
- Legacy CompareRunner / CM-PM KPI-flow uit ValidateWindow verplaatsen
  (ADR-0006 blijft).
- Navigatie “spring naar volgende bevinding” (slice 88 follow-up).
- Server/SMB portfolio scan (epic GRILL_DECISIONS §5 v2).
- Wijzigingen aan scrub-list items (`ltap_light`, killer/olifant, …).

**Fase B compare v1 specifiek uitgesteld naar slice-PRD:**

- Delta-tabel 20 rijen A/B/Δ (slice 56 out-of-scope hergebruikt).
- Handmatige FM-mapping UI (v1: id/fingerprint; manual mapping later).
- Persistente compare-sessie over app-restarts.
- Uniformeren/patches (fase C).

---

## Further Notes

### Voorgestelde slice-volgorde (implementatie)

```text
95a  Chrome-profiel in view-registry + orchestrator migrate (fase A)
95b  Derived refresh fase 2 — KPI/PBS-tree (technisch; parallel mogelijk)
96   Modelvergelijking v1 — twee projecten, balanced FM split (fase B)
97   Uniformeren v1 — review-only + audit (fase C)
98   Monte Carlo run-modus v1 (fase D)
99   FM delete + ValidateWindow retirement tranche 1 (fase E)
```

Nummering 95a/b is indicatief; `to-issues` mag splitsen op tracer bullets.

### Relatie bestaande documentatie

- **Slice 56/60/ADR-0007:** A/B op **één project** (runs/scenario's); fase B
  extend naar **twee projecten** — geen conflict, wel hergebruik slot-seam.
- **Slice 79:** view-registry wordt **bron van chrome** (besluit #1).
- **Slice 50/41:** orchestrator-ontvlechting blijft parallel; ratchet forceert
  extractie.
- **Epic parity/portfolio/MC:** MC scope en library dedup blijven geldig;
  **prioriteit** wordt hier herordend: compare vóór MC (besluit #4).
- **CONTEXT.md:** voeg bij implementatie toe: **vergelijkingswerkruimte**,
  **uniformeringsvoorstel**, **chrome-profiel** (glossary-only, geen implementatie).

### HILT vóór grote merges

- Push/merge slices 88–94 + visuele QA 91/93.
- Haarlem meekoppel-handcheck (slice 55-04) onafhankelijk van deze roadmap.
- Compare v1: handmatige workflow op twee echte klantprojecten vóór `done`.

### Risico's

| Risico | Mitigatie |
|--------|-----------|
| Compare v1 scope creep (uniformeren + compare) | Fase B expliciet read-only diffs |
| Registry chrome te rigide voor LCC/LTAP presets | `lcc_preset` patroon hergebruiken |
| Dual-project geheugen | Lazy load B; unload bij sluiten compare |
| MC + UI refresh coupling | Job runner buiten orchestrator tick |
| ValidateWindow retirement te vroeg | Parity checklist + ADR |

### Test-seams (bevestiging t.o.v. sessie)

De in deze PRD genoemde seams volgen AGENTS.md (adapter test-first, views niet
test-gestuurd) en sluiten aan op slice 88/90/91/93-prior art. Geen nieuwe
seams lager dan nodig; compare use-cases bewust Qt-vrij op adapter-niveau.
