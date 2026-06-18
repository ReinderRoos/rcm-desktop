# PRD — Slice 76: Werkruimte-menubalk + sneltoetsen

**Status:** ready-for-agent
**Voorganger:** slice 62 (werkruimte-panelen), slice 74 (NB-filter FM-detail), slice 75 (kolom-fit)
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van een `/grill-with-docs`-sessie (2026-06-11). Wens 3 van 5.
> Landt ná slice 74/75 zodat het menu reeds afgeronde acties bedraadt.

---

## Problem Statement

`ResultsWorkspaceWindow` heeft **geen menubalk**; alle bediening zit in
opeengestapelde knoppenrijen (`_build_toolbar`, modus-control, top10-subbar, …).
Het scherm oogt vol, en weergave-toggles zoals **Component-kolom (PBS-boom)** en
het **KPI-overzicht** zijn losse knoppen zonder sneltoets. De analist mist een
rustige, voorspelbare plek voor weergave-opties en kan toggles niet via het
toetsenbord bedienen.

## Solution

Vanuit de gebruiker gezien:

- Er komt een klassieke **menubalk** boven het venster. Een aantal knoppen
  verhuist daarheen, zodat het scherm schoner oogt.
- Een **Views-menu** bevat aan/uit-vinkbare items voor weergave-toggles —
  minimaal **PBS-boom zichtbaar** en **KPI-overzicht** — die de huidige toestand
  spiegelen.
- Elke gemigreerde actie krijgt een **logische sneltoets**.
- Een naar het menu verplaatste toggle heeft **geen dubbele knop** meer op het
  scherm: het menu-item is de enige bediening.

---

## Zoom-out: modulekaart

```
        ResultsWorkspaceWindow  (QMainWindow)
                 │  menuBar()  (NIEUW: QMenuBar)
                 ▼
   Menubalk-spec (Qt-vrij)  ── menu's, items, checkable, sneltoetsen
                 │  bindt op
                 ▼
   bestaande handlers / workspace-state
     PBS-boom:  _on_pbs_toggle  (lokale widget-zichtbaarheid)
     KPI:       set_kpi_collapsed_in_lcc  (workspace-state)
```

Betrokken seams (domeintaal → bestand):

- **Werkruimte-venster** — `rcm_desktop/views/results_workspace_window.py`
  (`_build_toolbar`, `pbs_toggle_button`/`_on_pbs_toggle`, `kpi_collapse_button`/
  `_on_kpi_collapse_toggled`). Hier komt `menuBar()` + `QAction`s; gemigreerde
  knoppen worden verwijderd.
- **Werkruimte-state** — `rcm_desktop/adapter/results_workspace_state.py`
  (`kpi_collapsed_in_lcc`, `set_kpi_collapsed_in_lcc`). KPI-toggle hangt hier al;
  PBS-zichtbaarheid is vandaag **lokaal** (`pbs_toggle_button`) en wordt
  meegenomen.
- **Menubalk-spec (NIEUW, Qt-vrij)** — een data-beschrijving van menu's → items
  (label, checkable, sneltoets, action-id), zodat de structuur + sneltoetsmap
  test-baar is zonder Qt.

---

## Implementation Decisions

### Besloten ontwerpkeuzes (grilling)

- **Gebalanceerde migratie (`balanced`).** Niet álle knoppen verhuizen. Naar het
  menu gaan de **weergave-/navigatie-toggles** en bestandsacties die logisch in een
  menu thuishoren; **werk-kritische, frequent gebruikte** knoppen (run-slots,
  validate/project inladen, compare) blijven op de toolbar zichtbaar.
- **PBS-boom-toggle bevestigd (`confirm`).** Het Views-item **PBS-boom zichtbaar**
  toggelt de component-kolom/PBS-zijbalk; aangevinkt = zichtbaar.
- **Menu vervangt knop (`menu_replaces_button`).** Een naar het menu verplaatste
  toggle verliest zijn losse schermknop; het menu-item is de enige bediening (geen
  dubbele state-bron).
- **Sneltoetsmap bevestigd (`confirm_map`).** Zie de map hieronder.

### Voorgestelde menustructuur + sneltoetsmap

> Bevestigd in de grilling als "logische" map; definitieve labels volgen
> `messages`-conventie. Sneltoetsen volgen Qt `QKeySequence`-tekst.

| Menu | Item | Checkable | Sneltoets | Bestaande handler/seam |
|------|------|-----------|-----------|------------------------|
| **Bestand** | Project inladen… | nee | `Ctrl+O` | `_start_validate` |
| **Bestand** | Open RCM-Cost export… | nee | `Ctrl+I` | `_open_rcm_cost_export` |
| **Bestand** | Afsluiten | nee | `Ctrl+Q` | `close()` |
| **Beeld (Views)** | PBS-boom zichtbaar | ja | `Ctrl+B` | `_on_pbs_toggle` |
| **Beeld (Views)** | KPI-overzicht | ja | `Ctrl+K` | `set_kpi_collapsed_in_lcc` (geïnverteerd) |
| **Beeld (Views)** | Kolommen bijsnijden | ja | `Ctrl+Shift+C` | slice 75 `<Bijsnijden>` (indien aanwezig) |
| **Analyse** | Faalwijzen-grid… | nee | `Ctrl+G` | `_open_batch_faalwijzen_grid` |
| **Analyse** | Modelinstellingen… | nee | `Ctrl+,` | `_open_model_settings` |
| **Analyse** | Rapport genereren… | nee | `Ctrl+R` | `_open_report_generation` |

Toolbar **blijft**: run-slot A/B, compare-toggle, project-pad/kiezen, modus-control,
top10-subbar (incl. NB-combo).

### Seam-keuze

- **Menubalk-spec** als Qt-vrije data (lijst van menu's met items: `action_id`,
  `label`, `checkable`, `shortcut`, default-checked-bron). Een pure builder/validator
  maakt dit test-baar: unieke sneltoetsen, geen dubbele action-ids, checkable-items
  hebben een state-bron.
- De **binding** (QAction's aanmaken, `setCheckable`, `setShortcut`, signalen op
  bestaande handlers) blijft venster-side (bind-only) — pure view, niet test-first.
- **PBS-zichtbaarheid naar state:** omdat het menu-item de enige bron wordt, wordt
  de PBS-zichtbaarheid een expliciete (eventueel gepersisteerde) toestand i.p.v.
  alleen een lokale knop-checked. Houd het minimaal: het menu-item ↔ zijbalk-
  zichtbaarheid synchroon.

### Architectuurprincipes (AGENTS.md)

- UI/kern-decoupling blijft; geen `rcm_core`-aanraking.
- De Qt-vrije menubalk-spec is test-first; de QAction-binding is pure view.
- Houd `results_workspace_window.py` onder het regelbudget (≤2000, gate
  `test_slice62_panel_gate.py`): overweeg de spec + builder in een eigen module.

---

## User Stories

1. Als RCM-analist wil ik een menubalk boven het venster, zodat het scherm rustiger
   oogt en ik bediening op een voorspelbare plek vind.
2. Als analist wil ik onder "Beeld" een aan/uit-vinkbaar item **PBS-boom zichtbaar**,
   zodat ik de component-kolom toon of verberg.
3. Als analist wil ik onder "Beeld" een aan/uit-vinkbaar item **KPI-overzicht**,
   zodat ik het KPI-paneel toon of inklap.
4. Als analist wil ik dat de vinkjes in het menu de huidige toestand spiegelen,
   zodat ik zie wat aan staat.
5. Als analist wil ik **`Ctrl+B`** voor PBS-boom en **`Ctrl+K`** voor KPI-overzicht,
   zodat ik toggles met het toetsenbord bedien.
6. Als analist wil ik dat een naar het menu verplaatste toggle geen losse knop meer
   heeft, zodat er geen verwarrende dubbele bediening is.
7. Als analist wil ik dat frequent gebruikte run-/validate-/compare-knoppen op de
   toolbar blijven, zodat mijn kern-workflow snel blijft.
8. Als analist wil ik bestandsacties (project inladen, RCM-Cost openen, afsluiten)
   in een **Bestand**-menu met sneltoetsen, zodat ze logisch gegroepeerd zijn.
9. Als analist wil ik dat alle sneltoetsen uniek en conflictvrij zijn, zodat geen
   actie een andere overschrijft.

---

## Testing Decisions

Goede tests toetsen **extern gedrag** aan de seam.

- **Primaire seam (Qt-vrij): de Menubalk-spec + validator.**
  1. Sneltoetsen zijn uniek; geen dubbele `action_id`.
  2. Checkable-items (PBS-boom, KPI-overzicht, Kolommen bijsnijden) hebben een
     gedefinieerde state-bron.
  3. De spec bevat de besloten items met de besloten sneltoetsen (golden map).
- **pytest-qt (venster):**
  - `menuBar()` bestaat met de menu's Bestand/Beeld/Analyse.
  - Het Views-item "PBS-boom zichtbaar" toggelt `pbs_sidebar`-zichtbaarheid; het
    vinkje volgt de toestand.
  - Het Views-item "KPI-overzicht" toggelt het KPI-paneel via
    `set_kpi_collapsed_in_lcc`.
  - De gemigreerde losse knoppen bestaan niet meer (of zijn niet zichtbaar).
  - Sneltoetsen triggeren de juiste handler.
- **Prior art:** `validate_window.py` (heeft al `QSettings`/menu-achtige structuur),
  `tests/test_desktop_results_workspace_window.py` (PBS-toggle, KPI-collapse).

---

## Out of Scope

- Volledige migratie van álle toolbarknoppen naar het menu (alleen de
  gebalanceerde subset).
- Een configureerbare/aanpasbare sneltoets-editor.
- Contextmenu's of een command-palette.
- Wijzigingen aan wat de toggles inhoudelijk doen (alleen verplaatsing + sneltoets).

## Further Notes

- "KPI-overzicht" in het menu is de **geïnverteerde** `kpi_collapsed_in_lcc`
  (aangevinkt = zichtbaar/uitgeklapt).
- Het item "Kolommen bijsnijden" is alleen zinvol als slice 75 gemerged is; anders
  weglaten of disablen.
- Volgorde: eerst de Qt-vrije menubalk-spec + validator (issue 01), dan de
  QAction-binding + knop-migratie + state-sync (issue 02).
