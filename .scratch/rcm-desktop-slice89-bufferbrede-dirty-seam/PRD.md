# PRD: Buffer-brede dirty-seam op EditingHost (slice 89)

**Triage-label:** `ready-for-agent`

## Problem Statement

Als analist bewerk ik invoer in meerdere Input-tabellen (Faalwijzen, REV-taken,
Effecten, Taakgroepen, …) via het generieke entiteiten-grid. Wanneer ik de tool
afsluit of een FM-editor open, controleert de **nette afsluitprocedure** alleen
of het *faalwijzen*-grid onopgeslagen wijzigingen heeft. Wijzigingen in alle
andere Input-tabellen worden niet gedetecteerd: de tool sluit zonder waarschuwing
en mijn werk gaat verloren.

Daarnaast spreekt de dirty-dialoog over "het faalwijzen-grid", wat misleidend is
zodra de wijziging in een andere tabel zit.

## Solution

De waarheidsbron voor "de bewerkingsbuffer is dirty" verschuift naar
`edit_dirty_global` uit de **tabulaire editing-pipeline** (kern). Die vlag wordt
al na elke `apply_rows` over *alle* entiteiten bijgewerkt en is daarmee per
definitie buffer-breed. `EditingHost.is_grid_dirty()` — de bestaande seam die de
afsluitprocedure en de dirty-guards gebruiken — gaat op deze vlag steunen in
plaats van op de faalwijzen-specifieke digest van `FaalwijzenEditService`.

Opslaan en verwerpen vanuit de dirty-dialoog werken voortaan ook buffer-breed:
verwerpen herstelt *alle* dirty entiteiten naar `edit_original`, opslaan commit
de hele buffer. De dialoogteksten worden generiek
("onopgeslagen invoerwijzigingen" conform CONTEXT.md), met een
contextafhankelijke annuleerknop ("Niet afsluiten" bij afsluiten,
"Editor annuleren" vóór een FM-editor).

## User Stories

1. Als analist wil ik bij het afsluiten van de tool gewaarschuwd worden als *welke Input-tabel dan ook* onopgeslagen wijzigingen heeft, zodat ik geen werk verlies.
2. Als analist wil ik bij het afsluiten kunnen kiezen tussen opslaan, verwerpen en annuleren, zodat ik zelf bepaal wat er met mijn wijzigingen gebeurt.
3. Als analist wil ik dat "opslaan" vanuit de dirty-dialoog de *hele* bewerkingsbuffer commit, zodat ook wijzigingen in niet-zichtbare tabellen behouden blijven.
4. Als analist wil ik dat "verwerpen" vanuit de dirty-dialoog *alle* dirty entiteiten terugzet naar de laatst gecommitte staat, zodat de buffer daarna aantoonbaar schoon is.
5. Als analist wil ik vóór het openen van een FM-editor gewaarschuwd worden bij onopgeslagen invoerwijzigingen in welke entiteit dan ook, zodat de editor niet start op een halfbewerkte buffer.
6. Als analist wil ik dat de dirty-dialoog spreekt over "onopgeslagen invoerwijzigingen" in plaats van "het faalwijzen-grid", zodat de tekst klopt ongeacht welke tabel ik bewerkte.
7. Als analist wil ik bij het afsluiten een annuleerknop "Niet afsluiten" zien (en vóór een editor "Editor annuleren"), zodat de knoptekst past bij wat er gebeurt.
8. Als analist wil ik dat het afsluiten zonder wijzigingen direct doorgaat zonder dialoog, zodat de procedure niet onnodig vertraagt.
9. Als analist wil ik dat een wijziging die ik terugdraai naar de oorspronkelijke waarde de buffer weer als schoon markeert, zodat ik geen valse waarschuwingen krijg.
10. Als analist wil ik dat na een succesvolle commit (promotie naar canoniek project) de buffer als schoon geldt, zodat afsluiten daarna zonder dialoog verloopt.
11. Als ontwikkelaar wil ik dat `EditingHost.is_grid_dirty()` de enige seam blijft waarmee views naar de dirty-status vragen, zodat afsluitprocedure en dirty-guards geen kernkennis nodig hebben.
12. Als ontwikkelaar wil ik dat de dirty-semantiek op één plek (de tabulaire editing-pipeline in de kern) gedefinieerd is, zodat er geen parallelle digest-administraties uiteenlopen.

## Implementation Decisions

Besluiten uit de grill-sessie (zie ook CONTEXT.md: **Nette afsluitprocedure**,
**Onopgeslagen invoerwijzigingen**):

- **Waarheidsbron**: `edit_dirty_global` uit de tabulaire editing-pipeline is de
  bron van waarheid voor buffer-brede dirty-status. De per-service digest in
  `FaalwijzenEditService`/`EntityEditService` blijft bestaan voor lokale
  view-doeleinden, maar de afsluitprocedure en dirty-guards steunen er niet
  meer op.
- **Seam**: `EditingHost.is_grid_dirty()` behoudt zijn signatuur maar leest
  voortaan `edit_dirty_global` uit de sessie van de actieve `EditingSession`.
  Geen actieve sessie betekent niet dirty.
- **Verwerpen is buffer-breed**: de discard-tak van de dirty-guard-policy
  herstelt alle entiteiten met `edit_dirty[entity] == True` naar hun
  `edit_original`-rijen en hervalideert, zodat `edit_dirty_global` daarna
  `False` is.
- **Opslaan is buffer-breed**: de save-tak commit de volledige buffer via het
  bestaande save-handler/commit-mechanisme op `EditingHost`; falen (bijv. door
  invoerbevindingen met severity fout) houdt het venster open met de bestaande
  waarschuwing.
- **Dialoogteksten generiek**: titel en tekst in de berichtencatalogus verwijzen
  naar "onopgeslagen invoerwijzigingen" over alle Input-tabellen; knoppen worden
  "Invoer opslaan" en "Invoer verwerpen".
- **Contextafhankelijke annuleerknop**: de dirty-guard krijgt een
  contextparameter zodat de annuleerknop "Niet afsluiten" toont in de
  afsluitprocedure en "Editor annuleren" vóór een FM-editor.
- **Planner ongewijzigd**: `plan_shutdown` en `ShutdownStep.RESOLVE_GRID_DIRTY`
  veranderen niet; alleen de `grid_dirty`-input wordt buffer-breed correct.
- **Geen ADR**: dit is een verdieping binnen bestaande besluiten (slice 78
  afsluitprocedure, tabulaire editing-pipeline); CONTEXT.md is al bijgewerkt.

## Testing Decisions

Goede tests toetsen extern gedrag op de bestaande seams, niet de interne
digest- of vlag-administratie:

- **`EditingHost.is_grid_dirty()`** (adapter, pytest): dirty na een wijziging in
  een niet-faalwijzen-entiteit (bijv. REV-taken); schoon na terugdraaien naar de
  oorspronkelijke waarde; schoon zonder actieve sessie; schoon na commit.
- **`resolve_dirty_choice`** (pure policy): discard met meerdere dirty
  entiteiten levert "proceed" en een aantoonbaar schone buffer; save-pad bij
  bevindingen met severity fout levert "warn_save_failed".
- **`plan_shutdown`** (pure planner): bestaande tests blijven groen; aanvullend
  een test dat een dirty niet-faalwijzen-entiteit tot
  `RESOLVE_GRID_DIRTY` in het plan leidt (via de host-seam).
- **Dialoogteksten/knoppen** (pytest-qt op de guard): generieke teksten en
  contextafhankelijke annuleerknop, naar analogie van bestaande
  grid-dirty-guard-tests.
- **Prior art**: tests rond slice 78 (afsluitprocedure), de bestaande
  dirty-guard-policy-tests en `tests/test_editing_pipeline.py`
  (`edit_dirty_global` na promotie).

Conform AGENTS.md: TDD op de adapterlaag; pure UI in `views/` niet
test-gestuurd, behalve waar pytest-qt-dekking al bestaat (guard-dialoog).

## Out of Scope

- Samenvoegen van `FaalwijzenEditService` en `EntityEditService` tot één stack
  (apart verdiepingskandidaat uit de architectuurreview).
- Wijzigingen aan de pass-throughs `input_revalidation_service` en de
  afsluit-planner zelf.
- Per-entiteit gedetailleerde weergave in de dirty-dialoog (welke tabellen
  precies dirty zijn); de dialoog blijft één generieke melding.
- Autosave of periodiek wegschrijven van de bewerkingsbuffer.
- Staleness van invoerbevindingen na verwerpen (hervalidatie via F7 blijft het
  bestaande mechanisme).

## Further Notes

- Dit PRD volgt uit de architectuurreview ("Verdiep dirty-seam op EditingHost",
  topkandidaat) en de aansluitende grill-sessie; de vocabulaire-besluiten staan
  al in CONTEXT.md.
- Let bij implementatie op de bestaande afspraak dat `mark_saved`/digest-logica
  in de services lokaal mag blijven; alleen de *host-seam* verandert van bron.
- Bij motorwijziging is geen JSON-vormwijziging voorzien; `CACHE_INPUTS_VERSION`
  hoeft niet omhoog.
