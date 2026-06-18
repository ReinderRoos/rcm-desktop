# PRD — Slice 78: Nette afsluitprocedure

**Status:** ready-for-agent
**Voorganger:** slice 46 (EditingHost / batch-grid dirty), slice 36 (achtergrondrunners), slice 77 (export-runs)
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van een `/grill-with-docs`-sessie (2026-06-11). Wens 4 van 5.
> Landt als laatste zodat alle eerdere slices (dirty-grid, runs, export) worden
> afgedekt.

---

## Problem Statement

`ResultsWorkspaceWindow.closeEvent` detacht alleen de tabelmodellen (anti-crash op
Windows) en doet daarna onvoorwaardelijk `event.accept()`. Er is **geen
afsluitbewaking**:

- Een **dirty batch-faalwijzen-grid** (onopgeslagen modelwijzigingen via
  `EditingHost`) gaat zonder waarschuwing verloren.
- Lopende **achtergrondruns** (`ValidateRunner`, `RunRunner`,
  `PresentationRebuildRunner`, `LCCWarmupRunner`, `CompareRunRunner`,
  `ReportRunner`) worden niet netjes geannuleerd; `main.py` heeft geen
  `aboutToQuit`-teardown.

De analist kan dus per ongeluk werk kwijtraken of de tool afsluiten terwijl er nog
een run draait.

## Solution

Vanuit de gebruiker gezien:

- Bij het sluiten controleert de tool of er **onopgeslagen modelwijzigingen** in het
  batch-grid zijn en biedt **opslaan / verwerpen / annuleren**.
- Als er nog een **achtergrondrun draait**, vraagt de tool om **bevestiging** en kan
  de analist kiezen om te **annuleren-en-wachten** (de run netjes afbreken) of toch
  open te blijven.
- Annuleren in beide gevallen houdt het venster gewoon open; pas na een schone
  afhandeling sluit de tool af zonder werk te verliezen of een run hard af te kappen.

---

## Zoom-out: modulekaart

```
        main.py  (QApplication.exec)
                 │  window.close() / OS-close
                 ▼
   ResultsWorkspaceWindow.closeEvent
                 │  vraagt Qt-vrije planner
                 ▼
   Afsluit-planner (NIEUW, Qt-vrij)
     input:  is_grid_dirty?  +  draaiende runners?
     output: ShutdownPlan  { grid: save|discard|cancel-vraag, busy: confirm-cancel-wait }
                 │  venster voert uit
                 ▼
   EditingHost.invoke_grid_save / runner.cancel / model-detach / accept|ignore
```

Betrokken seams (domeintaal → bestand):

- **Werkruimte-venster** — `rcm_desktop/views/results_workspace_window.py`
  (`closeEvent`, de runner-attributen `_runner`/`_run_runner`/… en de
  bestaande model-detach). Hier landt de afsluitbewaking.
- **Grid-dirty-bewaking** — `rcm_desktop/views/grid_dirty_guard.py`
  (`resolve_grid_dirty_before_editor`, `GridDirtyResolution`) +
  `rcm_desktop/adapter/editing_host.py` (`EditingHost.is_grid_dirty`,
  `invoke_grid_save`). Bestaand patroon (vóór editor openen) → hergebruiken vóór
  sluiten.
- **Achtergrondrunner** — `rcm_desktop/adapter/qt/background_runner.py`
  (`BackgroundRunner.cancel()`; `_update_run_buttons_enabled` weet al wie "busy" is).
- **Applicatie-entry** — `rcm_desktop/main.py` (`QApplication`,
  `aboutToQuit`-teardown ontbreekt).
- **Afsluit-planner (NIEUW, Qt-vrij)** — een pure functie/structuur die uit
  (`grid_dirty`, `busy_runners`) een **ShutdownPlan** afleidt, zodat de
  beslislogica test-baar is zonder Qt.

---

## Implementation Decisions

### Besloten ontwerpkeuzes (grilling)

- **Volledige scope (`full`).** De afsluitprocedure dekt **beide** risico's:
  (1) dirty batch-grid en (2) draaiende achtergrondruns.
- **Busy-run: bevestigen + annuleren-en-wachten (`confirm_cancel_wait`).** Bij een
  lopende run toont de tool een bevestiging; kiest de analist voor afsluiten, dan
  worden de runners **geannuleerd** (`cancel()`) en wacht de teardown netjes op
  beëindiging voordat het venster sluit. Annuleren houdt het venster open.

### Afsluit-volgorde (besloten)

1. **Grid-dirty eerst.** Is het batch-grid dirty → toon opslaan/verwerpen/annuleren
   (`resolve_grid_dirty_before_editor`-patroon). Annuleren → `event.ignore()`.
   Opslaan → `invoke_grid_save()`; mislukt opslaan → niet sluiten.
2. **Busy-runs daarna.** Draait er een runner → bevestiging; afsluiten gekozen →
   `cancel()` op alle actieve runners + wachten op beëindiging. Annuleren →
   `event.ignore()`.
3. **Teardown.** Bestaande model-detach (anti-crash) → `event.accept()`.

### Seam-keuze

- **Afsluit-planner** als klein Qt-vrij concept: pure functie
  `plan_shutdown(grid_dirty: bool, busy: bool) -> ShutdownPlan` met velden die
  zeggen *welke* prompts nodig zijn en *in welke volgorde*. Hiermee is de
  beslislogica volledig test-baar zonder venster.
- De **uitvoering** (QMessageBox-prompts, `invoke_grid_save`, `runner.cancel`,
  `event.ignore/accept`) blijft venster-side (pure view), maar leunt op de planner
  voor de beslissingen.
- **`main.py`:** voeg een `aboutToQuit`-teardown toe die als vangnet de runners
  cancelt (voor het geval de app langs een ander pad afsluit).

### Architectuurprincipes (AGENTS.md)

- UI/kern-decoupling blijft; de planner raakt geen `rcm_core`.
- De Qt-vrije afsluit-planner is test-first; de QMessageBox-/runner-binding is pure
  view.

---

## User Stories

1. Als RCM-analist wil ik bij het sluiten gewaarschuwd worden als ik onopgeslagen
   wijzigingen in het faalwijzen-grid heb, zodat ik geen werk verlies.
2. Als analist wil ik bij die waarschuwing kunnen kiezen tussen opslaan, verwerpen of
   annuleren, zodat ik de controle houd.
3. Als analist wil ik dat "annuleren" het venster open houdt, zodat ik kan
   doorwerken.
4. Als analist wil ik dat het sluiten wordt afgebroken als opslaan mislukt, zodat ik
   het probleem kan oplossen.
5. Als analist wil ik bij het sluiten met een lopende achtergrondrun een bevestiging
   krijgen, zodat ik niet per ongeluk een run afkap.
6. Als analist wil ik dat bij bevestigd afsluiten de lopende run netjes wordt
   geannuleerd en afgewacht, zodat er geen half-afgemaakte staat of crash ontstaat.
7. Als analist wil ik dat de tool, als er niets dirty is en niets draait, gewoon
   meteen sluit, zodat normaal afsluiten snel blijft.
8. Als analist wil ik dat de tool ook bij afsluiten via het OS (vensterkruis) of
   `Ctrl+Q` dezelfde bewaking toepast, zodat er geen achterdeur is.

---

## Testing Decisions

Goede tests toetsen **extern gedrag** aan de seam.

- **Primaire seam (Qt-vrij): de Afsluit-planner.**
  1. `grid_dirty=False, busy=False` → plan = direct sluiten.
  2. `grid_dirty=True` → plan vraagt grid-resolutie eerst.
  3. `busy=True` → plan vraagt busy-bevestiging.
  4. Beide → grid-prompt vóór busy-prompt (besloten volgorde).
- **pytest-qt (venster, gemonkeypatchte QMessageBox):**
  - Dirty grid + "annuleren" → `event.ignore()`, venster blijft open.
  - Dirty grid + "opslaan" → `invoke_grid_save()` aangeroepen; bij succes sluit het
    venster.
  - Opslaan mislukt → venster sluit niet.
  - Busy runner + "afsluiten" → `cancel()` op de actieve runner(s); venster sluit na
    beëindiging.
  - Niets dirty/niets draaiend → sluit direct (bestaande model-detach blijft).
- **`main.py`:** `aboutToQuit`-teardown cancelt actieve runners (vangnet).
- **Prior art:** `tests/test_background_runner.py` (runner-lifecycle, `qtbot`),
  `tests/test_desktop_results_workspace_window.py`, het
  `resolve_grid_dirty_before_editor`-patroon en `ValidateWindow.closeEvent`
  (bestaande unsaved-guard).

---

## Out of Scope

- Auto-save of crash-recovery van het hele project (alleen het batch-grid-dirty-pad).
- Een sessie-/vensterlayout-herstel bij heropenen (los van afsluiten).
- Wijzigingen aan de runners zelf, behalve het netjes aanroepen van `cancel()`.
- Bevestiging bij niet-grid-bewerkingen die al hun eigen save-pad hebben
  (FM-editor/model-settings committen al bij OK).

## Further Notes

- De FM-editor en modelinstellingen committen bij OK; de openstaande dirty-state die
  bij sluiten relevant is, is het **batch-faalwijzen-grid** via `EditingHost`.
- Volgorde: eerst de Qt-vrije afsluit-planner (issue 01), dan `closeEvent`-bedrading
  + runner-cancel (issue 02), dan `main.py` `aboutToQuit`-vangnet (issue 03).
