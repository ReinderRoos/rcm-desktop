# PRD: Consolidatie & edit-unificatie (slice 90)

**Triage-label:** `ready-for-agent`

Dit PRD bundelt *alle* aanbevelingen uit de architectuurreview van juni 2026
(assen: performance, security, stabiliteit, architectuur). Conclusie van die
review: performance en security zijn geen blockers; er ligt een dunne laag
stabiliteits- en architectuurwerk die nieuwe functionaliteit goedkoper en
veiliger maakt. Drie werkstromen:

- **A. Operationele consolidatie** — CI, minimale logging, tracker-sync,
  `.gitignore`.
- **B. Edit-unificatie** — één tabulaire edit-service, digest-administratie
  eruit, dirty-checks in views via `EditingHost`.
- **C. Werkruimte-venster ruimte** — extractie naar het bestaande
  panel-binding-patroon en de `rcm_core`-leaks in views dichten.

## Problem Statement

Als analist gebruik ik een tool die functioneel goed werkt, maar waarvan de
betrouwbaarheid op drie punten kwetsbaar is:

1. **Regressies worden alleen lokaal gevangen.** Er zijn ~1500+ tests maar geen
   CI: of een regressie opvalt hangt af van of de ontwikkelaar lokaal pytest
   draait vóór een push.
2. **Een fout in het veld is niet te diagnosticeren.** De run-, validate- en
   commit-paden vangen alle excepties breed af en tonen een generieke melding;
   de stack trace verdwijnt. Bij een probleem op een klantmodel is er niets om
   op terug te vallen.
3. **De volgende feature wordt onnodig duur.** Na slice 89 bestaan er twee
   dirty-modellen naast elkaar (het buffer-brede `edit_dirty_global` in de
   tabulaire editing-pipeline én de per-service content-digest in
   `FaalwijzenEditService`/`EntityEditService`). Het Validate-venster steunt
   nog zes keer op de digest-variant. Daarnaast zit het werkruimte-venster op
   10 regels van zijn ratchet-gate (2823 regels), waardoor de eerstvolgende
   feature die het venster raakt de gate breekt, en overtreden zeven
   runtime-imports van `rcm_core.*` in `views/` de UI/kern-decoupling-MUST uit
   AGENTS.md.

Tot slot loopt de issue-tracker achter (slices 87–89 staan op
`ready-for-agent` terwijl code en tests al gecommit zijn) en vervuilen
gegenereerde cache-/bak-bestanden de git-status.

## Solution

Eén consolidatieslice die de operationele gaten dicht en de halve unificatie
onder slice 89 afmaakt, zodat daarna zonder voorbehoud nieuwe functionaliteit
gebouwd kan worden:

**A. Operationele consolidatie.** Een CI-workflow (GitHub Actions, remote is
`ReinderRoos/rcm-desktop`) draait de testsuite bij elke push/PR; perf-tests
(`-m perf`) optioneel op schedule. De brede `except Exception`-paden in de
adapterlaag behouden de exception-keten: minimaal stdlib-logging van de stack
trace plus de oorzaak aan `UserFacingError` hangen. De tracker wordt
gesynchroniseerd (slices 87–89 naar done) en `.gitignore` dekt gegenereerde
cache-/bak-bestanden.

**B. Edit-unificatie.** `EntityEditService` (het generieke, config-gedreven
service uit slice 83) wordt de enige tabulaire edit-service; faalwijzen wordt
een configuratiegeval in plaats van een eigen klasse met ~200–300 regels
quasi-duplicaat. De per-service digest-administratie (`_saved_digest`,
`is_dirty`, `mark_saved`) verdwijnt: dirty-status loopt overal via de seam
`EditingHost.is_grid_dirty()` op `edit_dirty_global`, zoals slice 89 voor de
afsluitprocedure al deed. Het Validate-venster ruilt zijn zes
`_faalwijzen_edit.is_dirty()`-checks in voor de host-seam.

**C. Werkruimte-venster ruimte.** Vensterlogica wordt geëxtraheerd naar het
bestaande `panels/*_binding.py`-patroon tot er werkbare marge onder de gate
is, en de ratchet wordt verlaagd zodat de winst vastligt. De runtime-imports
van `rcm_core.*` in views verhuizen naar de adapterlaag of worden typing-only.

## User Stories

1. Als ontwikkelaar wil ik dat elke push en pull request automatisch de testsuite draait, zodat regressies niet afhangen van lokale discipline.
2. Als ontwikkelaar wil ik dat de CI-run de perf-gemarkeerde tests uitsluit maar deze optioneel op schedule draait, zodat de feedbackloop snel blijft en perf-regressies toch opvallen.
3. Als ontwikkelaar wil ik bij een mislukte run, validatie of commit de volledige stack trace in een log terugvinden, zodat ik een veldprobleem kan diagnosticeren.
4. Als analist wil ik bij een interne fout nog steeds een nette Nederlandse melding zien, zodat ik niet met een traceback geconfronteerd word.
5. Als ontwikkelaar wil ik dat `UserFacingError` de onderliggende oorzaak meedraagt, zodat foutafhandeling stroomopwaarts kan loggen zonder de gebruikerstekst te veranderen.
6. Als beheerder van de tracker wil ik dat slices 87–89 op done staan, zodat de tracker de werkelijke staat van de code weerspiegelt.
7. Als ontwikkelaar wil ik dat gegenereerde cache- en bak-bestanden door `.gitignore` gedekt zijn, zodat de git-status alleen echt werk toont.
8. Als ontwikkelaar wil ik één tabulaire edit-service voor alle Input-tabellen, zodat een bugfix of gedragswijziging op precies één plek landt.
9. Als ontwikkelaar wil ik dat faalwijzen een configuratiegeval van het generieke entiteiten-grid is, zodat er geen parallel faalwijzen-pad meer te onderhouden is.
10. Als ontwikkelaar wil ik dat de dirty-status van de bewerkingsbuffer uitsluitend via `EditingHost.is_grid_dirty()` opvraagbaar is, zodat er geen tweede dirty-model kan divergeren.
11. Als analist wil ik dat het Validate-venster exact hetzelfde dirty-gedrag vertoont als de afsluitprocedure, zodat opslaan/verwerpen overal dezelfde betekenis heeft.
12. Als analist wil ik dat na de unificatie alle bestaande grid-functies (bewerken, bulk-wijzigen, bevindingen, materialiseren voor run/save) ongewijzigd blijven werken, zodat de verdieping onzichtbaar is in mijn workflow.
13. Als ontwikkelaar wil ik dat het werkruimte-venster ruim onder zijn ratchet-gate komt, zodat de eerstvolgende venster-feature niet op de gate stukloopt.
14. Als ontwikkelaar wil ik dat de verlaagde regelstand in de ratchet-gate vastgelegd wordt, zodat het venster niet ongemerkt teruggroeit.
15. Als ontwikkelaar wil ik dat views geen runtime-imports van `rcm_core.*` meer hebben, zodat de UI/kern-decoupling-MUST uit AGENTS.md weer klopt en de adapterlaag de enige toegang tot de kern is.
16. Als ontwikkelaar wil ik een (gate-)test die nieuwe runtime-kernimports in views signaleert, zodat de regel niet opnieuw erodeert.
17. Als ontwikkelaar wil ik dat de parity-tests voor editing-schemas groen blijven tijdens de unificatie, zodat drift tussen domain model en editing-schema-registry uitgesloten is.
18. Als analist wil ik dat de tool tijdens en na deze slice geen zichtbaar gedrag verandert (behalve betere foutmeldingen in logs), zodat ik zonder herinstructie kan doorwerken.

## Implementation Decisions

Seams — bestaand boven nieuw, zo hoog mogelijk:

- **`EditingHost`** blijft dé seam voor dirty-status, opslaan en verwerpen
  (slice 89). Werkstroom B voegt geen nieuwe host-methoden toe maar verlegt
  callers (Validate-venster) naar deze seam.
- **`EntityEditService` + `EntityGridViewConfig`** is de overlevende
  interface van de unificatie. `FaalwijzenEditService` verdwijnt;
  faalwijzen-specifiek gedrag (o.a. materialize-blokkade bij fouten) wordt
  config- of subklasse-geval binnen het generieke service. Deletietest: het
  verwijderen van het faalwijzen-service concentreert complexiteit in het
  generieke service in plaats van haar te verplaatsen.
- **Digest-administratie vervalt.** `is_dirty`/`mark_saved`/`_saved_digest`
  op de edit-services verdwijnen; de tabulaire editing-pipeline
  (`edit_dirty_global`, per-entiteit `edit_dirty`) is de enige
  dirty-waarheidsbron. Dit herroept de slice 89-afspraak dat de digest "voor
  lokale view-doeleinden" mocht blijven — die bleek het resterende
  inconsistentie-risico.
- **Foutpaden behouden de keten.** Adapter-services die breed vangen (run,
  validate, fm-edit-commit, isograph-open-flow, model-settings,
  validate-runner) loggen de exceptie via stdlib `logging` en geven de
  oorzaak mee aan `UserFacingError`. Geen nieuw logging-framework; één
  logger-configuratie op applicatieniveau met logbestand naast de
  bestaande cache-bestanden.
- **CI als GitHub Actions-workflow**: testsuite met de bestaande
  pytest-configuratie (perf uitgesloten, conform `pyproject.toml`);
  Qt-tests headless (offscreen platform). Perf-marker als apart,
  niet-blokkerend job/schedule.
- **Venster-extractie volgt het bestaande patroon** `panels/*_binding.py`
  (slice 62): cohesieve clusters (per paneel of werkstroom) verhuizen uit het
  werkruimte-venster; de ratchet-constante gaat mee omlaag met de behaalde
  winst.
- **Kern-leaks**: runtime-imports van `rcm_core.*` in views worden typing-only
  (achter `TYPE_CHECKING`) of verhuizen naar een adapter-functie, per geval
  het kleinste dat de MUST herstelt. Een gate-test legt de regel vast.
- **Volgorde binnen de slice**: A eerst (CI vangt regressies van B en C),
  dan B, dan C.
- **Geen motorwijziging**: `rcm_core/` verandert niet van gedrag;
  `CACHE_INPUTS_VERSION` hoeft niet omhoog. Geen ADR nodig — alle besluiten
  zijn verdiepingen binnen bestaande besluiten (slice 83 generiek grid,
  slice 89 dirty-seam, slice 62 panel-extractie); wel CONTEXT.md bijwerken
  waar de term "tabulaire edit-service" landt.

## Testing Decisions

Goede tests toetsen extern gedrag op de seams, niet de interne administratie:

- **De interface is het testoppervlak.** Bestaande tests op
  `FaalwijzenEditService` worden geporteerd naar het generieke service (zelfde
  scenario's, zelfde asserts); de unificatie is geslaagd als beide testfamilies
  via één interface groen zijn.
- **`EditingHost.is_grid_dirty()`** dekt na werkstroom B ook de
  Validate-venster-scenario's: dirty na wijziging, schoon na verwerpen, schoon
  na opslaan (prior art: `tests/test_slice89_dirty_seam.py`).
- **Foutpaden**: per aangepast adapter-service één test dat een geforceerde
  interne fout (a) de bestaande `UserFacingError`-melding oplevert én (b) de
  oorzaak in de keten/het log aanwezig is (prior art: bestaande
  run-service-tests met seam-patch op `rcm_core.incremental_run as ir`).
- **Gates**: de bestaande ratchet-test op het werkruimte-venster krijgt de
  verlaagde baseline; een nieuwe gate-test scant `rcm_desktop/views/` op
  runtime-imports van `rcm_core` (prior art: `tests/test_slice62_panel_gate.py`).
- **Parity**: `tests/test_editing_schemas_parity.py` moet ongewijzigd groen
  blijven (AGENTS.md-contract).
- **CI bewijst zichzelf**: de workflow is af als de volledige suite headless
  groen draait op een schone runner.

Conform AGENTS.md: TDD op de adapterlaag (werkstroom B en de foutpaden);
pure UI-verhuizingen in `views/` (werkstroom C) niet test-gestuurd, de gates
bewaken daar het resultaat.

## Out of Scope

- **Lazy attach van Input-grids** (slice 87-follow-up): alleen oppakken als
  grote klantmodellen aantoonbaar pijn doen.
- **Dependency-pinning / lockfile**: reproduceerbaarheids-nice-to-have, geen
  kwetsbaarheid; apart op te pakken.
- **Volwaardige logging-/telemetrie-infrastructuur** (rotatie, niveaus per
  module, crash-reporting): deze slice doet alleen het minimale
  exception-keten-behoud.
- **Nieuwe functionaliteit** in de werkruimte of het Validate-venster.
- **Verdere opsplitsing van het werkruimte-venster** voorbij werkbare marge
  onder de gate; volledige ontvlechting is een eigen toekomstige slice.
- **Wijzigingen aan de tabulaire editing-pipeline in de kern** zelf
  (`rcm_core/editing/`): alleen de adapterlaag verandert.

## Further Notes

- Dit PRD volgt uit de architectuurreview van juni 2026 (twee verkenningen:
  architectuur-frictie en performance/stabiliteit/security). De review
  beoordeelde performance (slices 24–38) en security als niet-blokkerend.
- Werkstroom B is de logische voltooiing van slice 89: dat sliced de
  afsluitprocedure al naar `edit_dirty_global`, dit PRD haalt het tweede
  dirty-model definitief weg.
- Werkstroom C is bewust "tot werkbare marge", niet "perfect": de gate dwingt
  bij elke volgende venster-feature opnieuw extractie af, dus overinvesteren
  loont niet.
