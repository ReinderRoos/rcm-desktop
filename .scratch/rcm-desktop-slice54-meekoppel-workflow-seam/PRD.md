# PRD — RCM2 desktop slice 54 (meekoppel-workflow-seam + selectieve preview-audit)

**Status:** ready-for-agent  
**Versie:** 0.3  
**Triage-labels:** ready-for-agent  
**Type:** Architectuurverdieping + UX-flow hardening + audittrail (meekoppel)  
**Parent:** grill-me aanbevelingen (2026-06-02); sluit aan op meekoppel slices 39/40  
**Datum:** 2026-06-02

## Problem Statement

De meekoppel-flow in de resultatenwerkruimte heeft nu een functionele preview, maar mist interactieve taakselectie en robuuste traceerbaarheid.

Vanuit gebruikersperspectief leidt dit tot drie problemen:

1. Na PBS-selectie kan de gebruiker niet per zichtbare REV-taak expliciet kiezen wat wel/niet meegebundeld wordt.
2. Het previewvenster biedt geen snelle bulkacties (alles selecteren/deselecteren) op de gefilterde zichtbare set.
3. Bundelbesluiten zijn achteraf lastig te reconstrueren voor rapportage en vergelijking met ongebundeld onderhoud.

Daarnaast is er een architectuur/performance-risico:

- zonder centrale workflow-seam blijven overlay-mutaties versnipperd;
- zonder write-discipline kan auditlogging de UI vertragen bij grote selecties.

## Solution

Bouw slice 54 uit naar een complete, selectieve meekoppel-workflow met vier pijlers:

1. **Workflow-seam:** `MeekoppelWorkflowService` als enige orchestrator voor preview/apply.
2. **Selectiedialoog:** vervang tekstpreview door tabel met checkboxes, disabled-redenen, bulkselectie en live herberekende bundeldoeljaren.
3. **Traceerbaarheid:** schrijf per apply een gestructureerde bundel-audit (met globale bundel-id en baseline snapshot) naar overlay/project-state, plus compacte referentieregels in PM/FM-notities.
4. **Performance-guards:** audit alleen op apply in batch, cap op notitiegrootte, en lichte/lazy weergavemodus bij grote selecties.

Uitrol blijft achter tijdelijke feature-flag `meekoppel_workflow_v2` met sunset uiterlijk na slice 2 (tenzij expliciet verlengd).

## User Stories

1. Als analist wil ik per REV-taak in de preview kunnen aanvinken/uitvinken, zodat ik alleen relevante taken bundel.
2. Als analist wil ik dat de preview standaard alle geschikte zichtbare taken selecteert, zodat de basisflow snel blijft.
3. Als analist wil ik met een knop alles zichtbaar selecteren, zodat ik snel kan starten vanuit een gefilterde subset.
4. Als analist wil ik met een knop alles zichtbaar deselecteren, zodat ik gericht opnieuw kan opbouwen.
5. Als analist wil ik dat bulkselectie alleen op zichtbare gefilterde regels werkt, zodat acties voorspelbaar zijn.
6. Als analist wil ik dat handmatige vinkkeuzes behouden blijven tijdens filteraanpassingen binnen de sessie, zodat ik iteratief kan verfijnen.
7. Als analist wil ik dat niet-koppelbare taken zichtbaar blijven als disabled met reden, zodat ik begrijp waarom iets niet mee kan.
8. Als analist wil ik dat "Toepassen" disabled is bij minder dan twee geselecteerde verschuifbare taken, zodat ik geen foutlus krijg.
9. Als analist wil ik stabiele sortering op jaar en taaklabel, zodat de lijst scanbaar en consistent blijft.
10. Als analist wil ik dat keuzes resetten bij opnieuw openen van preview, zodat ik geen onverwachte oude selectie erfenis heb.
11. Als analist wil ik dat doeljaar live herberekent op de aangevinkte subset, zodat preview en werkelijk effect overeenkomen.
12. Als analist wil ik dat gekozen anchor (vroegste/laaste) altijd consequent op de huidige selectie werkt, zodat het gedrag logisch blijft.
13. Als analist wil ik dat apply alle geselecteerde sessietaken meeneemt, ook als sommige door filter tijdelijk verborgen zijn, zodat filter geen verborgen reset veroorzaakt.
14. Als analist wil ik een samenvattingsregel met geselecteerd/zichtbaar/verborgen/niet-selecteerbaar, zodat ik weet wat echt toegepast wordt.
15. Als analist wil ik dat annuleren/sluiten geen wijzigingen doorvoert, zodat preview transactioneel en veilig blijft.
16. Als reliability-analist wil ik bundelbesluiten later kunnen terugvinden met bundel-id, zodat ik analyses en verantwoording kan doen.
17. Als reliability-analist wil ik baseline-vs-na-bundeling per taak kunnen vergelijken, zodat effectrapportage betrouwbaar is.
18. Als product owner wil ik auditinformatie zowel vanuit PM als FM-context kunnen lezen, zodat rapportages niet afhankelijk zijn van een enkel perspectief.
19. Als product owner wil ik dat FM-notities compact blijven (max 1 regel per bundelactie), zodat informatie leesbaar blijft bij grote selecties.
20. Als ontwikkelaar wil ik dat overlay-mutaties alleen via workflow-service lopen, zodat state-drift verdwijnt.
21. Als ontwikkelaar wil ik een uniform `WorkflowResult`-contract, zodat viewcode geen businessregels dupliceert.
22. Als ontwikkelaar wil ik foutuitkomsten als `validation`/`blocked`/`system` coderen, zodat gedrag en messaging consistent testbaar zijn.
23. Als ontwikkelaar wil ik auditwrites alleen op apply en in batch uitvoeren, zodat interactie in de preview snel blijft.
24. Als ontwikkelaar wil ik notitiegroei begrenzen met cap-regels, zodat persist/render-kosten niet oplopen.
25. Als ontwikkelaar wil ik een lichte/lazy tabelmodus boven een volumedrempel, zodat grote selectie-interacties vloeiend blijven.
26. Als product owner wil ik stop/go kunnen beslissen op UX-metriek, architectuurmetriek, tests en demo, zodat vervolgslices evidence-driven zijn.

## Implementation Decisions

### Trajectkaders

- Een architectuurtraject in kleine slices met harde stop/go per slice.
- Prioriteit start bij hoogste leverage op Meekoppel/PlanningOverlay.
- Stop/go vereist zowel meetbare UX-winst als aantoonbare architectuurwinst.

### Scope slice 54 (hard)

- In scope:
  - meekoppel-paneel + preview/apply-workflow,
  - workflow-seam + uniform resultaatcontract,
  - checkbox-selectiepreview,
  - audittrail voor bundelbesluiten,
  - performance-guards voor grote selecties.
- Out of scope:
  - brede workspace-refactors buiten meekoppel,
  - verdiepende PBS-scope-sync buiten previewcontext,
  - niet-meekoppel productfeatures.

### Diepe modules en interfaces

- **MeekoppelWorkflowService**  
  Centrale orchestrator voor preview/apply en enige mutatiepad voor `PlanningOverlayState`.

- **MeekoppelPreviewSelectionModel**  
  Beheert sessieselectie, zichtbaarheidsfilter, bulkacties op zichtbare regels, tellerwaarden en apply-eligible set.

- **MeekoppelSelectionTableViewModel**  
  Levert tabelrijen met kolommen: checkbox, taak, huidig jaar, doeljaar, verschuiving, status/reden.

- **MeekoppelAuditService**  
  Schrijft gestructureerde bundel-events (globale bundel-id, timestamp, anchor, geselecteerde PM's, baseline/na) naar overlay/project-state en projecteert compacte notitieregels naar PM/FM.

- **MeekoppelPerformancePolicy**  
  Regels voor write-on-apply, note caps en threshold voor lichte/lazy tabelmodus.

### UX- en interactieregels

- Standaardselectie: alle zichtbare en geschikte regels aangevinkt.
- Bulkknoppen werken uitsluitend op zichtbare gefilterde regels.
- Keuzes blijven behouden binnen open preview-sessie.
- Selecties resetten bij opnieuw openen van de preview.
- Disabled taken blijven zichtbaar met concrete reden.
- Doeljaar herberekent live op aangevinkte subset volgens gekozen anchor.
- Apply werkt op volledige geselecteerde sessieset (ook tijdelijk verborgen regels).
- Samenvattingsregel boven de tabel is verplicht.
- Annuleren/sluiten heeft geen side effects.

### Audit- en traceermodel

- Per apply één globale bundel-id.
- Audit bevat minimaal:
  - bundel-id, timestamp, anchor, context (PBS/scope),
  - betrokken PM-taken,
  - baseline per taak (before),
  - resultaat per taak (after/shift),
  - eventuele skip/block-informatie.
- Schrijfscope:
  - volledige machine-leesbare audit in overlay/project-state,
  - compacte append-referentie in PM-notities,
  - maximaal één samenvattende append-regel per betrokken FM per bundelactie.

### Performance-keuzes

- Geen audit- of notitiewrites tijdens preview-interactie.
- Audit/notities alleen bij apply in één batch.
- Notitietekst capped (bijv. laatste N regels per object) om ongebreidelde groei te voorkomen.
- Grote selecties schakelen naar lichte/lazy modus boven drempel (richtwaarde >200 regels).

### Feature-flag governance

- Nieuwe flow achter `meekoppel_workflow_v2`.
- Flag-sunset uiterlijk na slice 2, tenzij expliciet verlengd met motivatie.

## Testing Decisions

Goede tests valideren observeerbaar gedrag via publieke interfaces, niet implementatiedetails.

### Testprincipes

- Test workflowuitkomst, niet interne helpercalls.
- Test selectiegedrag via publiek modelcontract.
- Test audit-output op structurele velden en mutatie-effecten, niet op interne storage details.
- Werk verticaal met tracer bullets (RED -> GREEN per gedrag), niet horizontaal per laag.

### Verplichte test-gate

1. Adapter-unittests voor `validation`/`blocked`/`system` workflowuitkomsten.
2. Integratietest voor preview -> apply happy flow met geselecteerde subset.
3. Regressietest die afdwingt dat view geen directe overlay-mutatie buiten workflow doet.

### Aanvullende tests

- Selectiemodeltests: default-selectie, filterpersistentie, bulk op zichtbare regels, apply-eligible teller.
- Previewreken-tests: live doeljaarherberekening voor beide anchors.
- Audit-tests: bundel-id, baseline snapshot, PM/FM projection, append-gedrag, FM-single-line policy.
- Performancegedrag-tests: write-on-apply-only en drempelgedrag voor lichte/lazy modus.

### Prior art

- Bestaande meekoppel adapter/view tests.
- Bestaande planning-overlay/what-if tests.
- Bestaande regressietests rond results workspace interactiepatronen.

## Stop/Go Criteria

Slice 54 krijgt alleen GO als alle criteria gehaald zijn:

1. UX-criterium: `clicks_selection_to_apply_success` daalt met vooraf vastgestelde target.
2. Architectuur-criterium: `overlay_mutation_sites_outside_workflow_service = 0`.
3. Kwaliteits-criterium: volledige test-gate slaagt.
4. Demo-criterium: vaste baseline-vs-v2 demo-run uitgevoerd en gedocumenteerd.

## Out of Scope

- Volledige redesign van resultatenwerkruimte buiten meekoppel.
- Persistente checkbox-keuze tussen preview-openingen heen.
- Realtime auditwrites tijdens preview-interactie.
- Diepe rapportage-UI voor auditanalyse binnen deze slice.

## Further Notes

- Deze PRD vervangt de eerdere v0.1 slice-brief als bron voor uitvoering in slice 54.
- Uitvoering blijft in kleine issue-slices met duidelijke afhankelijkheden en AFK/HITL scheiding.
- Auditfunctionaliteit is bewust ontworpen met performance-first writepolicy om regressies in interactieve preview te voorkomen.
- **Slice 55 (parent-rollup discovery)** moet afgerond zijn vóór issues **03+** van deze slice; zie `.scratch/rcm-desktop-slice55-meekoppel-discovery-parent-rollup/SLICE_MAP.md`.
- **Preview-inzicht (epic 03b, slices 03c–03g):** PRD `.scratch/rcm-desktop-slice54-meekoppel-workflow-seam/PRD-preview-insight.md` — hybride bundel-scope, trekker-regel, baseline/effectief-kolommen, locatietabel-tooltip; dialoog-inzicht achter `meekoppel_workflow_v2`. Issue **04** volgt na **03f**.
