# RCM2 desktop — domeinvocabulaire

Deze repo is de native desktop-variant (PySide6/Qt6) van RCM, gestart als fresh
copy-and-adapt van de RCM1-kern. Vocabulaire dat domein-experts en agents nodig
hebben om eenduidig te praten:

## Language

**Domain model (`rcm_core.models`)**
De canonieke dataclasses (`RCMProject`, `PBSItem`, `Faalwijze`, `PMTask`,
`EffectKlasse`, `FMResult`, `PBSResult`) en hun `to_dict()`/`from_dict()`. Bron
voor analytische run en serialisatie.

**PBS-volgorde**
Expliciet presentatieveld `PBSItem.volgorde` (int): sibling-volgorde in boom, tabellen
en rapportage. Gepersisteerd in `.rcm.json`, **uitgesloten** van globale digest en
FM-invoerhash (ADR-0013). Herordenen markeert dirty maar triggert geen her-run.

**Editing schema registry (`rcm_core.editing.schemas.ENTITY_SCHEMAS`)**
Bewuste tweede bron voor bewerkbare entiteiten in de UI: titels, `store_key`,
welke velden zichtbaar zijn, `field_types` (string-coerciion), `required_fields`,
en `fk_rules` voor validatie. Niet automatisch uit `models` gegenereerd.

**FK target (schema-backed)**
FK in `fk_rules` waarvan het doel óók in `ENTITY_SCHEMAS` staat. Geldige waarden
komen uit de in-memory edit-buffer voor die entiteit.

**FK target (project-backed)**
FK-doel zonder eigen rij in `ENTITY_SCHEMAS` (bv. `functies`, `task_groups`).
Geldige IDs komen uit `RCMProject` (zie `rcm_core.editing.validation.resolve_fk_set`).

**Tabulaire editing-pipeline**
De keten **initialiseren → bewerken (buffers) → valideren → materialiseren →
persist (disk) of run (analyse)**. Canoniek model in de UI-sessie zit onder
`rcm_core.editing.pipeline.CANONICAL_PROJECT_KEY`. Sessie is **injecteerbaar**:
`init_edit_state`, `apply_rows`, `validate_all_entities`, `build_project_from_state`
accepteren optioneel `session=dict`. In RCM2 is die injectie **verplicht** vanuit
`rcm_desktop.adapter` — geen Streamlit-`session_state`-aanname meer.

## Cache + run

**Globale digest** (`rcm_core.cache.compute_global_digest`)
Vingerafdruk over volledige canonieke `RCMProject.to_dict()` + `CACHE_INPUTS_VERSION`.
Bij mismatch: cache niet vertrouwen voor incrementele merge → alle faalwijzen opnieuw.

**FM-invoerhash** (`rcm_core.cache.compute_fm_hash`)
SHA256 over canonieke JSON-slice van de FM-relevante invoer (FM, gekoppeld PBS,
PM-taken, alle `task_groups`, volledige `config`, FM/PM-effectlinks, volledige
`pbs_items` voor effectieve leeftijd/multipliciteit).

**Run-orchestratie** (`rcm_core.incremental_run.run_incremental_analysis`)
Eén pad voor volledige en incrementele analytische run op een geladen `RCMProject`.
Combineert cache-seam met motor (`rcm_core.engine`).

**Adapter CLI** (`rcm_core.cli`)
Rookproef-tool boven de kern; subcommando's `validate`, `impact`, `run`, `fit`,
`bibliotheek-*`. Bewust geen `serve`, geen Monte Carlo in CLI. Excel **import**
alleen via desktop/adapter (ADR-0004), geen Excel in `rcm_core.cli`.

**Adapter Qt** (`rcm_desktop.adapter`)
Qt-zijdige run-orchestratie en model/view-bindings.

## Resultatenwerkruimte

**Resultatenwerkruimte-venster** (`ResultsWorkspaceWindow`)
Bind-only shell: past orchestrator-plannen toe op Qt-widgets, verbindt
signalen, en aliast panel-referenties op `self`. Modus-view-constructie
(`build_*_view`) zit niet in het render/bind-pad (slice 61).

**ResultsWorkspaceOrchestrator** (`rcm_desktop.adapter.results_workspace_orchestrator`)
Qt-vrije planner voor workspace snapshot-ticks. Composeert bestaande
`ResultsWorkspaceController` (run/validate blijft daar):
- `plan_ui_sync(prev, current)` → **WorkspaceUiSyncPlan** (toolbar, compare-chrome, collapse)
- `plan_render(...)` → **RenderPlan** (modus-DTO's: fm, bijdragen, lcc, compare)
- `plan_workspace_tick(...)` → **WorkspaceTickPlan** (ui_sync + render + split_depth)

**Werkruimte-panelen** (`rcm_desktop.views.panels`, slice 62)
Mechanisch geëxtraheerde widget-bomen per modus; event-handlers blijven
venster-side:
- **BijdragenWorkspacePanel** — chart-only Top 10, compare-kolommen
- **contribution_display_service** — Qt-vrije display-seam voor bijdragen-waarden (chart-labels)
- **FmDetailWorkspacePanel** — FM-tabel, inspector
- **LccWorkspacePanel** — what-if bar, meekoppel, chart/tables, compare
- **workspace_table_policy** — gedeelde tabel-header policy

Stretch line budget: `results_workspace_window.py` ≤2000 regels (gate:
`tests/test_slice62_panel_gate.py`).

**Werkruimte-menubalk** (`QMenuBar`)
Klassieke applicatie-menubalk boven het venster die schermknoppen overneemt en
sneltoetsen biedt. Het **Beeld-menu** bevat aan/uit-vinkbare items voor
weergave-toggles — minimaal **PBS-boom zichtbaar** (de component-kolom/PBS-zijbalk)
en **KPI-overzicht** — plus submenu's **Input** en **Output** met views uit de
view-registry. Een menu-item is de **enige** bediening voor een gemigreerde toggle
(geen dubbele knop). PBS-boom is de enige resterende Beeld-toggle.

**Werkruimte-zijde**
Conceptuele scheiding tussen **Input** (invoertabellen) en **Output**
(resultaatweergaves). De analist schakelt met `Ctrl+1` / `Ctrl+2`; per zijde
onthoudt de state de laatst gekozen view (**sticky per zijde**).

**Werkruimte-navigatierail**
Verticale bedieningsstrook rechts van het resultaatgebied (`detail_zone`):
Werkruimte-zijde (Input/Output) bovenaan — **onder elkaar** — daaronder de
actieve view-tabs uit de view-registry. De PBS-zijbalk blijft links;
scope-selectie en view-navigatie zijn zo visueel gescheiden. Vaste breedte
~160px (Input-bedieningslabels); Output houdt compacte rail-labels. Inklapbaar
gedrag is uitgesteld.

**Rail-label**
Weergavenaam van een view in de navigatierail. Los van het volledige
**view-label** (Beeld-menu, view-titel, tooltips). Komt uit de view-registry.

- **Output:** verkorte codes (KPI, LCC, LTAP, TopX).
- **Input:** bedieningslabels — leesbaar en kort, niet per se identiek aan het
  view-label: Faalwijzen, REV, Effect, Taakgroep, Correctief (registry-labels
  blijven formeel: «REV-taken», «Taakgroepen», «Correctief onderhoud»).

**View-titel**
Prominente kopregel direct boven het actieve view-inhoudsgebied
(`detail_zone`), met het volledige view-label uit de registry (bv.
«Top bijdragen», «LCC-plot», «Faalwijzen»). Geeft oriëntatie zonder de
navigatierail te dupliceren. Overlay- of sessiestatus (bv. what-if actief)
hoort **niet** in de view-titel maar in chrome-footer of statusstrip.

**Werkruimte-chrome-footer**
Horizontale bedieningsbalk direct onder het actieve view-inhoudsgebied
(niet onder de PBS-zijbalk, niet onder de navigatierail). Bundelt
view-chrome uit het chrome-profiel (`toolbar_family`): gedeelde controls
midden, view-specifieke filters rechts (bv. LCC-maatregeltypes onder
elkaar). Lichtgewicht LCC-planningbediening (what-if aan/uit, reset,
presets) hoort hier; zware planning-workflows (meekoppelkansen-tabel,
jaarverschuiving bij grafiekselectie) blijven in het inhoudsgebied.

Twee vaste zones: **midden** gedeelde chrome (metric, horizon, NB,
what-if-knoppen, overlay-status), **rechts** smalle kolom (~120px, altijd
gereserveerd) voor verticale view-specifieke filters — ook leeg bij views
zonder rechterstack, zodat bediening niet verspringt bij view-wissel.

**View-registry** (`workspace_view_registry`)
Qt-vrije declaratieve lijst van werkruimte-views: `view_id`, zijde, label,
sneltoets, volgorde, enabled. Voedt dropdown, Beeld-submenu's en
modus-mapping (legacy `MODE_*` blijft implementatiedetail).

**Chrome-profiel** (`WorkspaceChromeProfile`, slice 95)
Declaratieve capability-metadata per `view_id` in de view-registry:
toolbar-acties, filters en `toolbar_family` (`none` | `top10` | `lcc` | `fm` |
`input_grid`). De orchestrator **interpreteert** dit profiel i.p.v. ad hoc
view-checks.

**Vergelijkingswerkruimte**
Aparte workflow voor het naast elkaar laden en vergelijken van twee
`.rcm.json`-bestanden (baseline A, scenario B). Balanced split per faalwijze:
invoer én resultaten even zichtbaar. Niet de dagelijkse enkel-model navigatie
(ADR-0016).

**Uniformeringsvoorstel**
Review-only voorstel om verschillen tussen twee modellen te harmoniseren, met
expliciete bron (A→B of B→A). Pipeline:
`DifferenceSet → NormalizationProposal → UserReview → Patch → AuditTrail`;
geen automatische merge op lage drempel in v1.

**FM-resultaten**
Output-view (was: FM-detail): sorteerbare faalwijze-tabel plus **FM-inspector**
in de resultatenwerkruimte. Analist gebruikt deze view om **grootste bijdragen** aan
kosten en niet-beschikbaarheid te vinden (metric, sortering, effectfilter).
View-label in het Beeld-menu: **Top bijdragen**; rail-label: **TopX**. Geen aparte
Top-10-view meer.

**Top bijdragen-diagram**
Horizontaal Top-N staafdiagram in Top bijdragen (tabel/diagram-toggle). Toont
ranking van faalwijzen op de actieve metric. Geen LCC-tijdreeks — die hoort bij
LCC-plot (projectniveau) of FM-inspector (faalwijze-niveau).

**FM-inspector**
Read-only verificatiepaneel onder de FM-tabel in Top bijdragen. Alleen
beschikbaar in **tabelweergave** (niet in Top bijdragen-diagram). Wordt geopend
met **dubbelklik** op een rij (niet met enkele selectie). Bij open inspectiemodus:
de tabel toont een **contextvenster** van maximaal **drie rijen** (faalwijze
erboven, geselecteerde faalwijze, faalwijze eronder); aan de rand van de
gefilterde lijst alleen beschikbare buren (geen placeholders). Bij één of
twee rijen totaal: toon alle beschikbare. De volledige gefilterde lijst keert
terug na sluiten. Schakelen naar **Top bijdragen-diagram** sluit inspectiemodus
automatisch (inspector alleen in tabelweergave). Onder de tabel: lifecycle-samenvatting, reconcile-status
en een **LCC-plot op faalwijze-niveau** (metric/NB/horizon gekoppeld aan de
zelfde filters als de hoofdtabel): **faalmomenten** en **niet-beschikbaarheid**
als enkelvoudige reeks per kalenderjaar; **kosten** als **CM + PM gestapeld**
per jaar (PM-serie via adapter, analoog aan project-LCC). **Sluiten** herstelt tabelweergave zonder
inspector; **pijl omhoog/omlaag** stapt naar vorige/volgende faalwijze in de
gefilterde lijst. **Bewerken…** in het inspector-paneel opent de faalwijze-editor
voor de geselecteerde FM (bewuste stap na validatie; dubbelklik opent geen editor).

**LCC-plot**
Output-view (was: Tijdsplot): LCC-jaargrafiek met what-if-planning en
meekoppelkansen.

**LTAP (preset-view)**
Output-view op hetzelfde LCC-panel als LCC-plot, met hard preset **CM uit**:
correctief onderhoud is niet zichtbaar in de curve en CM-bediening is binnen
LTAP niet bedienbaar. Metric, jaren en overige type-filters werken door;
terugschakelen naar LCC-plot herstelt de opgeslagen CM-toestand. Geen port van
`ltap_light` (scrub-list); zie ADR-0012.

**Kolom-fit-modus**
Per-tabel weergave-keuze voor kolombreedtes: **passend** (kolommen schikken zich
naar de inhoud) versus **bijgesneden** (vaste maximumbreedte, te lange tekst
ge-elideerd met "…"). De gekozen modus is **persistent** (`QSettings`) per tabel.
De FM-detail-tabel biedt een **Bijsnijden**-schakelaar; de policy is herbruikbaar
voor andere werkruimte-tabellen.

**Tabel-filterrij**
Onder de kolomkoppen van een **Output**-tabel (FM-resultaten): per kolom een
filterveld. Tekstkolommen filteren op deelstring (hoofdletterongevoelig);
booleankolommen via ja/nee/alles; numerieke kolommen via expressies (`>`,
`>=`, `<`, `<=`, `=`, bereik `a..b`, kaal getal = exact). Filters combineren
als EN; een wisknop maakt alle filters leeg. De rijtelling toont
gefilterd/totaal. Ongeldige numerieke expressies tonen alle rijen met visuele
foutmarkering op het veld. Filterwaarden worden niet tussen sessies bewaard.
Herbruikbare seam: `table_filter_parser` + `TableColumnFilterProxy`. Het
**entiteiten-grid** gebruikt deze volledige filterrij **niet** (zie ADR-0014).

**Entiteiten-grid**
Generiek, schema-gedreven bewerkbaar grid in de Input-zijde van de
resultatenwerkruimte. Kolommen, typen en validatie komen uit de **Editing schema
registry**; per view alleen configuratie (entiteit, kolompreset, optionele
projectie). Vijf Input-views: Faalwijzen, REV-taken (`pm_tasks`), Effecten,
Taakgroepen en Correctief onderhoud (projectie op faalwijzen met CM-kolomset).
Bewerken loopt via de **tabulaire editing-pipeline**; kolomkeuze is persistent
per view via `QSettings`. Presentatiefilter op Input: **PBS-scope** (waar van
toepassing) plus één **globale zoekbalk** per view — geen per-kolom filterrij.
Zie ADR-0014.

**PBS-scope op Input**
De actieve PBS-subtree-selectie uit de werkruimte-boom (`scope_id`) filtert
**presentatie** van PBS-gebonden Input-views: Faalwijzen en Correctief via
directe `pbs_id`; REV-taken via `fm_id` → faalwijze. Effecten en Taakgroepen
zijn projectbreed (geen PBS-koppeling); bij actieve scope toont een subtiele
statusregel dat PBS-scope daar niet geldt. Zelfde presentatie-semantiek als
Output (geen deelrun; bewerkingsbuffer blijft volledig). Hergebruikt
subtree-bepaling als Output (`collect_pbs_subtree_ids`).

**Invoerbevinding**
Geconstateerd probleem met een rij of cel in een Input-view, met ernst **fout**
(rood, blokkeert opslaan/run) of **waarschuwing** (geel, nooit blokkerend).
Drie bronnen: de tabulaire editing-pipeline, projectvalidatie
(`validate_project`/`validate_aannamen`) en consistentie-bevindingen (slice 49).
De cel-markering (kleur + tooltip) is de *presentatie* van een invoerbevinding;
is de bijbehorende kolom verborgen, dan landt de markering op de sleutelkolom
van de rij.
_Vermijd_: edit-error, warning, finding (los, zonder bron of ernst)

**Controleer invoer (hervalidatie)**
Handmatige, altijd buffer-brede hervalidatie van alle invoerbevindingen,
bediend via één menu-item in het Analyse-menu (F7). Geen knop per grid;
alle aangekoppelde entiteiten-grids verversen mee.

**Nette afsluitprocedure**
Het gecontroleerde sluiten van de tool: vóór teardown wordt (1) bij
**onopgeslagen invoerwijzigingen** in de bewerkingsbuffer (alle Input-tabellen,
niet alleen faalwijzen) een keuze gevraagd: opslaan, verwerpen of annuleren, en
(2) bij een lopende achtergrondrun een **bevestiging met annuleren-en-wachten**
getoond, zodat geen onopgeslagen modelwijziging of half-afgemaakte run verloren
gaat. Annuleren houdt het venster open.

**Onopgeslagen invoerwijzigingen**
Wijzigingen in de **bewerkingsbuffer** die nog niet zijn gecommit naar het
canonieke project (of weggeschreven naar schijf). Geldt buffer-breed over alle
entiteiten in de tabulaire editing-pipeline, niet per Input-view apart.
_Vermijd_: grid dirty, batch-grid dirty (te smal — impliceert alleen faalwijzen)

## FM-verificatie & spot-check

Drie lagen om **één faalwijze (FM)** te controleren — van streng naar interactief:

1. **pytest / CLI** — Strengste, reproduceerbare verificatie. Gebruik fixtures en
   motor-`FMResult` (inclusief `horizon_profile` waar aanwezig), reconcile-tests
   (`tests/test_nmf_schedule.py`, adapter unit-tests). Leg regressies hier vast
   vóór je in de UI kijkt.

2. **Resultatenwerkruimte, Top bijdragen** — Standaard interactief pad na slice 34.
   - **Verifiëren (read-only):** **dubbelklik** op een FM-rij opent **inspectiemodus**
     (FM-inspector): lifecycle-totalen, reconcile-status, **FM-invoerhash**, en
     **LCC-plot op faalwijze-niveau** (vervangt de jaartabel). Alleen in
     tabelweergave; contextvenster van drie rijen in de tabel; pijltjes
     navigeren; sluiten herstelt de volledige tabel.
   - **Bewerken:** primair vanuit **Input → Faalwijzen** (en verwante
     invoertabellen) via de modale **faalwijze-editor** (`FmEditorDialog`).
     Secundair: knop **Bewerken…** in FM-inspector na validatie in Top bijdragen.
     Top bijdragen-dubbelklik opent geen editor.

3. **Batch faalwijzen-grid** (slice 46) — homogene modelfouten (faaltype, NMF, MTTF,
   …) batch-corrigeren via schema-gedreven grid + `apply_bulk_change`.
   **ValidateFaalwijzenPanel** wordt gehost in zowel ValidateWindow als
   resultatenwerkruimte (menuknop). Beide hosts delen dezelfde buffer via
   **EditingHost** (`EditingSession` + save/commit entry); er is geen aparte
   globale grid-registry meer. PRD: `.scratch/rcm-desktop-slice46-fm-edit-fase2/`.

4. **Legacy ValidateWindow** (`--legacy-validate` / `RCM_LEGACY_VALIDATE=1`) —
   **Projectcockpit** voor valideren, run, LTAP/PM what-if en hetzelfde batch-grid.
   De modale FM-editor blijft het primaire pad voor volledige FM-scope-bewerking
   (slice 44); ValidateWindow is niet de hoofdroute voor diep FM-editwerk.

Kalenderjaar in de inspector gebruikt dezelfde mapping als LCC/Tijdsplot:
`modeljaar` + horizonindex. Jaarreeks in de UI is **presentatie-proxy**
(zelfde pad als Top 10/LCC), geen tweede motorberekening.

**Faalwijze-editor openen (Input)**
Op **Input → Faalwijzen**: **dubbelklik** op een rij opent de faalwijze-editor
voor die FM. Overige Input-views (REV, Effect, Taakgroep, Correctief) krijgen
eigen dubbelklik→editor zodra entity-specifieke editors bestaan; tot die tijd
grid-only zonder dubbelklik-editor.

## Effectimpact (slice 70)

**Niet-beschikbaarheid (totaal)**
Totale downtime over alle faalwijzen: CM + PM + verborgen NB, als uren of % van
de lifecycle. Default Top 10-metric; ongewijzigd t.o.v. slice 33.

**Effectimpact**
Bijdrage van één **effectklasse** aan de analyse, uitgesplitst in CM- en
PM-deel. De **maat en het label** hangen af van de **effectcategorie** — niet
elke effectklasse is “niet-beschikbaarheid”. In Top 10 en Tijdsplot kiest de
analist metric **Niet-beschikbaarheid**, **Faalmomenten** of **Kosten**; bron
is **Component** of **Faalwijze** (geen aparte bron Effectklasse meer, slice 71).

**NB-effectfilter**
Multi-select op niet-beschikbaarheidseffectklassen (alleen categorie
beschikbaarheid) plus de **Detectie-/verborgen-NB-restpost**. Lege selectie =
totale NB (slice 33-semantiek). De selecteerbare verzameling vormt een **echte
partitie** van de totale NB: alles aangevinkt = totaal, elke deelselectie ≤
totaal. Gedeeld tussen Top 10, Tijdsplot **en de FM-detail-tabel** (downtime-kolom
+ inspector) via workspace state.

**Detectie-/verborgen-NB-restpost**
Selecteerbare pseudo-effectklasse in de NB-effectfilter die de
detectievertraging / verborgen niet-beschikbaarheid vertegenwoordigt — downtime
die niet aan een fysieke effectklasse toe te rekenen is. Sluit het gat tussen de
som van de effect-specifieke NB-delen en de totale NB, zodat de delen exact naar
het totaal sommeren. De echte effectklassen behouden hun definitie (`RF × downtime
× failures` + PM-uren); RF-fracties worden niet hernormaliseerd, en de getoonde
filterwaarde wordt geclampt op ≤ totaal voor zeldzame RF-overlap.

**Effectcategorie**
Genormaliseerde groep op `EffectKlasse.categorie` (afgeleid uit AW
`RcmEffects.Type`): minimaal **beschikbaarheid**, **veiligheid**, **kosten**,
**overig**. Bepaalt welke maat en UI-label bij een effectklasse horen.

**AW effecttype**
Ruwe waarde uit AW `RcmEffects.Type` (bv. `Schutten`, `VGM`, `Keren`).
Bewaard naast de genormaliseerde effectcategorie voor traceerbaarheid en
AW-vergelijking; niet identiek aan effectcategorie.

**NB per effect (beschikbaarheid)**
Alleen voor effectcategorie **beschikbaarheid** (bv. Schutten, functieverlies):
effect-specifieke downtime in uren of % — CM-deel als `RF × downtime × failures`,
PM-deel als gedegradeerde uren via PM-effectlinks.

**NB-bucketreeks (per FM)**
Gepresenteerde niet-beschikbaarheid per horizonbucket voor één faalwijze, voor een
gegeven NB-effectfilter (leeg = totaal incl. verborgen NB; gevuld = som van de
geselecteerde effectklassen). Enige bron-van-waarheid waaruit zowel de **Top 10**-
scalar als de **Tijdsplot**-curve reduceren: de scalar is een reductie over de
buckets (levensduur-som, jaargemiddelde of één kalenderjaar), de Tijdsplot is de
reeks zelf. Garandeert dat Top 10 en Tijdsplot consistent zijn en dat een
deelselectie nooit groter is dan het totaal.

**Veiligheidsincidenten (veiligheid)**
Alleen voor effectcategorie **veiligheid** (bv. VGM): incidenten-equivalent
(`verwachte faalgebeurtenissen × RF`), geen downtime-uren. Label in UI is
**niet** “Niet-beschikbaarheid”.

**Incidenten-equivalent**
Verwacht aantal faalgebeurtenissen gewogen met RF; eenheid “incidenten”, geen
uren. Motor-ruwe CM-effectbijdrage vóór categorie-specifieke presentatie.

**CM-effectbijdrage / PM-effectbijdrage**
Effectimpact uitgesplitst naar correctief (CM) versus preventief (PM). CM-deel
is incidenten-equivalent; PM-deel is gedegradeerde uren. Presentatielaag
combineert per effectcategorie tot één leesbare maat.

## Rekenmodi (werkruimte)

**Run-modus**
Keuze per werkruimte-sessie: **analytisch** (deterministische motor, default) of
**Monte Carlo** (stochastische herhalingen). In MC-modus voedt de MC-run **Top 10,
LCC (P50)** en **FM-resultaten (banden)**; analytische slot blijft apart beschikbaar
bij terugschakelen. N via `monte_carlo_n`; seed via `monte_carlo_seed` (leeg =
willekeurig). MC op achtergrond met voortgang; annuleren gooit partial resultaten weg.

**MC-presentatie-pariteit**
Wat de UI belooft t.o.v. analytische presentatie in MC-modus: horizon-conforme
FM-kolommen (default Ø per jaar), niet-vlakke LCC/NB-jaarcurves voor aging-faalwijzen,
en compare-slots die MC-resultaten tonen zonder verborgen analytical session-state.
_Avoid:_ "parity" zonder horizon-qualifier; numerieke gelijkheid MC P50 lifecycle-totalen
↔ analytisch punt (P50 is verdeling-median, analytisch is puntschatting).

**Scenariovergelijking (werkruimte)**
Twee bevroren scenario's (referentie + variant) binnen **één project**: **Start
analyse** (live run) → **Extra scenario** (bevriest scenario 1, configureert variant)
→ **Vergelijk scenario's** (Top 10, LCC, FM split). Maximaal twee scenario's; sessie-only.
Gescheiden van **Vergelijk modellen…** (twee `.rcm.json`-bestanden).

**RCM2 presentatielaag**
Visuele en interactieve huid rond de resultatenwerkruimte: Delta Pi-huisstijl,
layout-shell (topbar, navigatie, statusstrip, footer) en view-specifieke
presentatieregels. Rekeneenheden en adapter-DTO's blijven leidend; geen parallel
mock-datamodel. Dekking: **hele** resultatenwerkruimte (Input- én Output-views).
Layout-shell v2 (navigatierail, chrome-footer): zie ADR-0020.
**ValidateWindow** blijft buiten scope tot slice 99 (retirement).

**KPI-overzicht**
Output-view (`output.kpi_overview`) in de view-registry: compacte tabel met
project-KPI-totalen, gefilterd op actieve PBS-scope. Geen overlay boven andere
views — de analist navigeert ernaar via navigatierail, Beeld → Output of
sneltoets (`Ctrl+K`). Chrome-footer leeg (`toolbar_family: none`).

**StatusStrip**
Persistente statusregel in de werkruimte: validatiestatus, MC-modus en
run-voortgang. Blijft zichtbaar tijdens analyse; geen kortdurende toast-meldingen.

**Werkruimte-footer**
Kortdurende statusmeldingen onderaan het venster (opslaan, export, run voltooid,
fout-toast). Persistente state blijft in de StatusStrip.

**Faalwijze-analyse (UI-blauwdruk)**
Werknaam uit de RCM2 UI-spec voor **FM-resultaten** tijdens **scenariovergelijking**:
twee kolommen (scenario 1 / scenario 2), metric-gestuurde kolomkeuze, optionele
tabel↔diagram-weergave, highlight bij grote verschillen. Geen aparte view in de
view-registry — hergebruikt de FM-output-view plus compare-chrome. **FM-inspector**
is in v1 niet beschikbaar tijdens scenariovergelijking; diepere faalwijze-inzage
via single-run FM-resultaten.

**Metric-gestuurde kolomkeuze**
In scenariovergelijking op FM-resultaten toont elke scenario-kolom alleen de **actieve
metriek** naast faalwijze-identificatie; overige metriek-kolommen zijn verborgen.
Single-run FM blijft multi-kolom.

**Optionele NMF/RF-kolommen**
In Faalwijze-analyse kunnen **NMF**- en **RF**-kolommen naast identificatie en actieve
metriek getoond worden; default **verborgen**, analist schakelt expliciet in.

**Uitgelijnde scenario-rijen**
In Faalwijze-analyse delen beide scenario-kolommen **dezelfde rijvolgorde** op basis
van de unie van faalwijzen (S1 ∪ S2), gesorteerd op scenario-1-waarde van de actieve
metriek. Ontbrekende waarden in één scenario tonen een lege cel; %-highlight geldt
alleen waar beide scenario's een S1>0-waarde hebben.

**Tabel↔diagram-weergave**
In Faalwijze-analyse wisselt analist **exclusief** tussen uitgelijnde tabel (twee
scenario-kolommen) en één gepaard horizontaal staafdiagram (S1/S2 per faalwijze).
Default tabel; zelfde rijvolgorde en highlight-regels in beide modi.

**Scenario-kleur**
Vaste presentatiekleur per scenario in **scenariovergelijking**: scenario 1 =
Delta Pi-rood, scenario 2 = Delta Pi-magenta. Geldt voor kolomkoppen en
chart-series in Top 10, LCC en FM — visuele herkenning, geen rekeneenheid.

**Delta Pi-huisstijl**
Organisatie-palet en typografie voor de RCM2-presentatielaag (navy topbar,
surface-grijs, scenario-kleuren). Tokens zijn productvast; technische toepassing
via centraal Qt-thema in de desktop-app. Typografie: Calibri Light / Calibri met
Segoe UI-fallback op systemen zonder Calibri.

**App-wordmark**
Organisatie- en productidentiteit links in de werkruimte-topbar (Delta Pi + RCM2).
In v1 tekstlabels volgens huisstijl; latere logo-asset vervangt de labels zonder
layout-contract te wijzigen.

**FM-onzekerheidsband**
Presentatie van MC-uitkomsten per faalwijze: **P10 / P50 / P90** per FM-metriek
(kosten, downtime, faalgebeurtenissen) over N simulatiepaden. Faalmomenten zijn
stochastisch; kosten/downtime-parameters per pad deterministisch (v1).

## RCM-Cost round-trip (ADR-0011)

**AW-bron-sidecar** (`<project>.rcm.source.xlsx`)
Bij Excel-import bewaarde kopie van de originele Availability-Workbench-workbook,
opgeslagen naast het `.rcm.json`-project (zelfde conventie als `.rcm.cache.json`).
Het pad staat in `import_settings` (`source_workbook_path`). Bron-van-waarheid voor
de 15 sheets die RCM2 niet modelleert, zodat export volledige fidelity behoudt.

**RCM-Cost export (round-trip)**
Het terugschrijven van het in RCM2 bewerkte model naar een AW-leesbare workbook,
door de **AW-bron-sidecar** te her-emitteren en alleen de door RCM2 bewerkte velden
(must-v1 sheets) te **patchen**. Bewerkte waarden patchen op bestaande rijen; in
RCM2 nieuw aangemaakte entiteiten worden **toegevoegd**; ontbrekende rijen worden
**niet** verwijderd maar **gemeld**. Ontbreekt de sidecar, dan blokkeert de export
met een file-picker om de bron te lokaliseren.

## Wat ontbreekt t.o.v. RCM1 (bewust)

- **Killer/olifant-classificatie** is verwijderd. `PBSResult` heeft geen
  `is_unavailability_killer`/`is_cost_elephant`. Geen `classify_results`.
  Gebruikers leiden rangordening zelf af uit `total_cost_eur`,
  `total_downtime_hr`, `unavailability_pct`. Zie supersedes-ADR.
- Streamlit-shell, runflow-contract, dashboard-modules: niet geporteerd; UI
  wordt opnieuw opgebouwd in PySide6.
- **RCM-Cost import (bootstrap):** RCM-Cost export → `.rcm.json` via de
  resultatenwerkruimte (ADR-0004). Geen gevolgkosten-import; PM-effectlinks alleen
  volgens PM-spike. Round-trip-export terug naar Availability Workbench: zie
  **RCM-Cost export (round-trip)** + ADR-0011 (slice 77).
- Monte Carlo UI/motor, LTAP-light: buiten scope tracer-bullet.
- Meekoppelkansen: toegestaan via **ADR-0005** (adapter-only in resultatenwerkruimte LCC+what-if); geen scrub-list-port van RCM1-module; `ltap_light` blijft out.
