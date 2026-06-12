# PRD — Slice 79: View-registry + Input/Output-navigatie

**Status:** ready-for-agent
**Voorganger:** slice 76 (werkruimte-menubalk), slice 62 (werkruimte-panelen)
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van de `/grill-with-docs`-sessie (2026-06-11), besluiten 1 en 2.
> **Tracer bullet** van de reeks 79–86: alle volgende slices registreren hun
> view in de registry die hier ontstaat.

---

## Problem Statement

De werkruimte kent vandaag één platte modus-keuze (Top 10 / Tijdsplot /
FM-detail) via een segmented control. De analist wil op detailniveau
**invoer en uitvoer scheiden**: invoertabellen (faalwijzen, REV-taken,
effecten, taakgroepen, correctief onderhoud) en uitvoerweergaves (Top 10,
LCC-plot, LTAP, FM-resultaten) zijn conceptueel verschillende werelden, maar
de huidige navigatie biedt daarvoor geen plek. Nieuwe views toevoegen betekent
nu: knoppenrij uitbreiden + ad-hoc `setVisible`-logica in het venster.

## Solution

Vanuit de gebruiker gezien:

- Bovenin de werkruimte komt een **Input | Output**-schakelaar die de
  modusknoppen vervangt.
- Naast de schakelaar staat een **dropdown** met de views van de actieve
  zijde. Output: *Top 10*, *LCC-plot* (was: Tijdsplot), *LTAP*,
  *FM-resultaten* (was: FM-detail). Input: *Faalwijzen*, *REV-taken*,
  *Effecten*, *Taakgroepen*, *Correctief onderhoud*.
- Het menu **Beeld** krijgt submenu's Input en Output met dezelfde views.
- Per zijde onthoudt de werkruimte de laatst gekozen view (**sticky per
  zijde**): wie van Output → Input → Output schakelt, komt terug waar die was.
- Sneltoetsen: `Ctrl+1` (Input), `Ctrl+2` (Output), `Ctrl+Alt+1..n` (view
  binnen de actieve zijde).

In deze slice mappen de **bestaande drie views** op Output (met hernoemde
labels); Input-views en LTAP volgen in latere slices maar krijgen hier al hun
plek in de registry (desnoods als placeholder/disabled).

---

## Zoom-out: modulekaart

```
        ResultsWorkspaceWindow  (QMainWindow)
            │ zijde-schakelaar + view-dropdown + Beeld-submenu's
            ▼
   View-registry (Qt-vrij, NIEUW)  ── zijde, view-id, label, sneltoets, volgorde
            │ gegenereerd: menu-items, dropdown-inhoud, QStackedWidget-mapping
            ▼
   Werkruimte-state  ── actieve zijde + sticky view per zijde
            ▼
   bestaande panelen (Top10 / LCC / FM-resultaten)
```

Betrokken seams (domeintaal → module):

- **View-registry (NIEUW, Qt-vrij)** — datastructuur naar het patroon van
  `WORKSPACE_MENU_SPEC`: per view een `view_id`, zijde (`input`/`output`),
  label (uit `messages`), sneltoets en volgorde; plus een pure validator
  (unieke ids, unieke sneltoetsen, labels aanwezig).
- **Werkruimte-state** (`results_workspace_state`) — nieuwe state: actieve
  zijde + sticky view-id per zijde; vervangt op termijn `MODE_*`-switching
  als navigatiebron.
- **Werkruimte-orchestrator** (`results_workspace_orchestrator`) — plant
  zichtbaarheid op basis van (zijde, view-id) i.p.v. alleen `mode`.
- **Menubalk-spec** (`workspace_menu_spec`) — Beeld-submenu's worden
  gegenereerd uit de registry, niet handmatig gedupliceerd.

---

## Implementation Decisions

- **Input|Output vervangt de modusknoppen** (besluit 1). De segmented control
  voor Top10/Tijdsplot/FM-detail verdwijnt; navigatie = zijde-schakelaar +
  view-dropdown + Beeld-menu. Eén bron van waarheid: de registry.
- **Sticky view per zijde** (besluit 1): de werkruimte-state onthoudt per
  zijde de laatst actieve view; zijde-switch herstelt die.
- **Eén Qt-vrije view-registry** (besluit 1) genereert menu, dropdown én
  paneel-stack-mapping. Views registreren zich declaratief; het venster bindt
  alleen (bind-only, zoals de menubalk-binding van slice 76).
- **Naming** (besluit 2): Output-view heet **"FM-resultaten"** (was
  FM-detail); de tijdsplot heet **"LCC-plot"**; de Input-tabel heet
  **"Faalwijzen"**. Alle labels via `messages`.
- **Interne mode-constanten blijven** (`MODE_BIJDRAGEN`, `MODE_LCC`,
  `MODE_FM_DETAIL`) als implementatiedetail achter de registry; geen big-bang
  hernoeming van state-velden in deze slice.
- **Sneltoetsen**: `Ctrl+1`/`Ctrl+2` voor zijde, `Ctrl+Alt+1..n` voor views
  binnen de zijde (volgorde = registry-volgorde). Registreren via de
  bestaande menubalk-spec zodat de uniciteitsvalidatie ze meeneemt.
- **Input-zijde in deze slice**: de registry kent de vijf Input-views al
  (ids + labels), maar de panelen zelf landen in slice 83; tot die tijd toont
  de Input-zijde een nette placeholder of zijn de items disabled. LTAP idem
  (slice 82).
- **Persistentie**: actieve zijde + sticky views in `QSettings`, naar het
  patroon van bestaande werkruimte-instellingen.
- **CONTEXT.md**: nieuwe termen *Werkruimte-zijde*, *View-registry*,
  *FM-resultaten*, *LCC-plot* worden in deze slice toegevoegd (de slice
  introduceert de begrippen).

## User Stories

1. Als RCM-analist wil ik bovenin de werkruimte kiezen tussen **Input** en
   **Output**, zodat invoer en uitvoer duidelijk gescheiden zijn.
2. Als analist wil ik per zijde een **dropdown met views**, zodat ik snel de
   juiste tabel of plot kies.
3. Als analist wil ik onder menu **Beeld** submenu's Input en Output met
   dezelfde views, zodat menu en dropdown consistent zijn.
4. Als analist wil ik dat de werkruimte per zijde mijn **laatst gekozen view
   onthoudt**, zodat heen-en-weer schakelen geen context verliest.
5. Als analist wil ik `Ctrl+1`/`Ctrl+2` om van zijde te wisselen, zodat ik
   zonder muis kan navigeren.
6. Als analist wil ik `Ctrl+Alt+1..n` om binnen een zijde van view te
   wisselen, zodat schakelen tussen Top 10, LCC-plot en FM-resultaten één
   toetscombinatie is.
7. Als analist zie ik de namen **FM-resultaten** en **LCC-plot** consequent
   in dropdown, menu en titels, zodat de terminologie eenduidig is.
8. Als analist wil ik dat mijn zijde- en view-keuze bewaard blijft tussen
   sessies, zodat de tool opent waar ik gebleven was.
9. Als ontwikkelaar wil ik dat een nieuwe view alleen een registry-entry
   nodig heeft, zodat menu, dropdown en stack automatisch volgen.
10. Als analist wil ik dat nog niet beschikbare views (Input-tabellen, LTAP)
    zichtbaar maar disabled zijn, zodat ik weet wat eraan komt zonder op een
    dode knop te klikken.

## Testing Decisions

Goede tests toetsen extern gedrag aan de hoogst mogelijke seam.

- **Primaire seam (Qt-vrij): de view-registry + validator.**
  1. Golden test: registry bevat de besloten zijden/views/labels/sneltoetsen.
  2. Validator: unieke `view_id`s, unieke sneltoetsen (ook t.o.v. de
     menubalk-spec), elke view heeft een zijde en label.
- **Orchestrator (Qt-vrij):** zijde-switch levert het juiste view-plan;
  sticky-gedrag (Output→Input→Output herstelt de Output-view).
- **pytest-qt (venster):** zijde-schakelaar + dropdown sturen de paneel-stack;
  Beeld-submenu's bestaan en spiegelen de actieve view; sneltoetsen werken;
  de oude segmented control bestaat niet meer.
- **Prior art:** `tests/test_slice76_workspace_menu_spec.py` (golden spec +
  validator), `tests/test_results_workspace_orchestrator.py` (plan-tests),
  `tests/test_desktop_results_workspace_window.py` (venster-smoke).

## Out of Scope

- De Input-panelen zelf (slice 83) en LTAP-gedrag (slice 82).
- FM-resultaten-tabelwijzigingen (slice 80).
- Verwijderen van de interne `MODE_*`-constanten of een
  state-machine-herontwerp.
- Een command-palette of configureerbare sneltoetsen.

## Further Notes

- Houd `results_workspace_window.py` onder het regelbudget (gate
  `test_slice62_panel_gate.py`): registry + builder in eigen adapter-module.
- De hernoeming Tijdsplot → LCC-plot raakt bestaande `messages`-constanten en
  tests die op het label asserteren; pas die in dezelfde slice aan.
- Slice-volgorde: 79 → 80/81 (parallel mogelijk) → 82 → 83 → 84 → 85 → 86.
