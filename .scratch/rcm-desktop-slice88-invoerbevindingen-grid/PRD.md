# PRD — Slice 88: Invoerbevindingen in het entiteiten-grid

**Status:** done
**Voorganger:** slice 83/87 (entiteiten-grid + performance), slice 49 (FM-editor consistentie-bevindingen), slice 46 (batch-grid)
**Datum:** 2026-06-12
**Triage:** `done`

> Synthese van de `/grill-with-docs`-sessie (2026-06-12). Vastgelegd in
> `CONTEXT.md` (termen **Invoerbevinding**, **Controleer invoer**) en
> **ADR-0015** (ernst-dualiteit). Brengt drie validatiebronnen samen als
> cel-markeringen met tooltips in de Input-views.

---

## Problem Statement

De analist ziet pas of het model fouten, onlogische of inconsistente waarden
bevat wanneer hij een cel bewerkt (editing-pipeline), de Validate-knop gebruikt
(projectvalidatie) of de modale FM-editor opent (consistentie-bevindingen,
slice 49). In de invoertabellen zelf is daarvan niets zichtbaar: een vers
geladen project met bestaande fouten toont een schoon grid, en kruis-entiteit-
inconsistenties (bv. NMF zonder testtaak) blijven onzichtbaar tot run-tijd.
Daardoor ontdekt de analist problemen laat, buiten de context waar hij ze zou
oplossen.

## Solution

Vanuit de gebruiker gezien:

- Elke Input-view (Faalwijzen, REV-taken, Effecten, Taakgroepen, Correctief
  onderhoud) markeert cellen met een **invoerbevinding**: **rood** voor fouten
  (blokkeren opslaan/run, huidig gedrag), **geel** voor waarschuwingen (nooit
  blokkerend). Rood wint bij samenloop op één cel.
- De **tooltip** van een gemarkeerde cel toont álle meldingen voor die cel,
  gegroepeerd op ernst.
- Markeringen zijn er **direct bij het openen** van een grid — ook voor fouten
  die al in het geladen project zaten, zonder dat eerst een cel bewerkt hoeft
  te worden.
- Consistentie-bevindingen uit de FM-editor (aging zonder REV-taak,
  PM-bundeladvies, …) verschijnen nu ook in de grids, als gele markering op de
  kolom waar de analist het probleem typisch oplost.
- Projectvalidatieregels verschijnen in het grid: regels binnen één rij als
  fout, kruis-entiteit-regels als waarschuwing (bij run/Validate blijven die
  laatste onverminderd hard — ADR-0015). Aannamen-meldingen zijn altijd
  waarschuwingen.
- Is de bijbehorende kolom verborgen, dan landt de markering op de
  **sleutelkolom** van de rij zodat de bevinding zichtbaar blijft.
- **Analyse → Controleer invoer (F7)** hervalideert de volledige
  bewerkingsbuffer en ververst alle aangekoppelde grids. Geen knop per grid.
- Het rijtelling-label in de grid-toolbar toont een passieve
  **bevindingen-telling** ("2 fouten, 3 waarschuwingen") voor de huidige view.

---

## Zoom-out: modulekaart

```
   rcm_core.editing.validation  ── error_obj + severity ("error"/"warning")
        │  validate_entity_rows (bestaand, fouten)
        │  validate_all_entities bij session-load (NIEUW gedrag)
        ▼
   EditingSession / edit_errors  ── één opslag voor fouten én waarschuwingen
        ▲
        │  waarschuwingen-injectie (buffer-breed)
   input_grid_findings (adapter, Qt-vrij, NIEUW)
        │  • slice-49 consistentie-bevindingen → (entiteit, rij, canonieke kolom)
        │  • kruis-entiteit validate_project-regels → waarschuwing
        │  • enkel-rij validate_project-regels → fout
        │  • validate_aannamen → waarschuwing (aanname_*-kolom)
        │  • fallback: sleutelkolom bij verborgen/ontbrekende kolom
        ▼
   EntityEditService → EntityRowView.field_errors (met severity)
        ▼
   EntityTableModel  ── BackgroundRole rood/geel, ToolTipRole gegroepeerd
        ▼
   Entiteiten-grid-panel  ── bevindingen-telling in toolbar-label
        ▲
   workspace_menu_spec  ── analysis.revalidate_input, "Controleer invoer", F7
```

## User Stories

1. Als RCM-analist wil ik dat cellen met een foutieve waarde rood gemarkeerd
   zijn in de invoertabellen, zodat ik fouten zie zonder eerst te bewerken of
   te valideren.
2. Als analist wil ik dat cellen met een onlogische of inconsistente waarde
   geel gemarkeerd zijn, zodat ik aandachtspunten kan onderscheiden van harde
   fouten.
3. Als analist wil ik bij een gemarkeerde cel een tooltip met alle
   constateringen voor die cel, gegroepeerd op ernst, zodat ik precies weet
   wat er aan de hand is.
4. Als analist wil ik dat een cel met zowel een fout als een waarschuwing rood
   toont, zodat de ernstigste melding nooit ondersneeuwt.
5. Als analist wil ik dat markeringen direct zichtbaar zijn bij het openen van
   een Input-view op een vers geladen project, zodat bestaande modelfouten
   niet verborgen blijven tot de eerste bewerking.
6. Als analist wil ik dat foutmarkeringen na een celbewerking direct worden
   bijgewerkt, zodat ik onmiddellijk feedback krijg (bestaand gedrag blijft).
7. Als analist wil ik dat fouten opslaan en run blokkeren zoals nu, zodat de
   bestaande kwaliteitspoort intact blijft.
8. Als analist wil ik dat waarschuwingen nooit blokkeren tijdens het bewerken,
   zodat ik een tijdelijk inconsistente tussenstand kan passeren (eerst de FM
   aanpassen, dan de REV-taak).
9. Als analist wil ik dat een kruis-entiteit-regel bij run/Validate een harde
   fout blijft, zodat ik nooit per ongeluk een run doe op een aantoonbaar
   inconsistent model (ADR-0015).
10. Als analist wil ik consistentie-bevindingen uit de FM-editor (aging zonder
    REV, REV zonder aging, PM-bundeladvies) ook in de grids zien, zodat ik ze
    niet alleen per toeval in de modale editor tegenkom.
11. Als analist wil ik dat zo'n bevinding op de kolom staat waar ik het
    probleem typisch oplos, zodat de markering me naar de juiste plek leidt.
12. Als analist wil ik dat een bevinding op de sleutelkolom van de rij landt
    wanneer de eigenlijke kolom verborgen is, zodat kolomkeuze geen bevindingen
    verstopt.
13. Als analist wil ik aannamen-meldingen (ontbrekende motivatie) als gele
    markering zien, op de `aanname_*`-kolom indien zichtbaar en anders op de
    sleutelkolom, zodat ik documentatie-achterstand in beeld houd.
14. Als analist wil ik enkel-rij-regels uit de projectvalidatie (bv. sigma bij
    random-faaltype, negatieve kosten) als fout in het grid zien, zodat ik ze
    binnen de rij direct kan oplossen.
15. Als analist wil ik via Analyse → Controleer invoer (F7) de volledige
    buffer hervalideren, zodat ik na een reeks bewerkingen alle bevindingen
    kan verversen — inclusief kruis-entiteit-waarschuwingen.
16. Als analist wil ik dat die hervalidatie alle openstaande Input-views
    ververst, niet alleen de zichtbare, zodat de buffer één consistente
    waarheid toont.
17. Als gevorderde gebruiker wil ik de hervalidatie via een sneltoets bedienen,
    zodat ik mijn workflow niet hoef te onderbreken.
18. Als analist wil ik per Input-view een bevindingen-telling in de toolbar,
    zodat ik na laden of hervalidatie zie of er iets gevonden is — ook als de
    getroffen cellen buiten beeld gescrold zijn.
19. Als analist wil ik dat PBS-scope en zoekbalk de markeringen niet
    beïnvloeden (gefilterde rijen behouden hun bevindingen), zodat presentatie-
    filters geen valse geruststelling geven.
20. Als analist wil ik dat de telling de bevindingen van de hele view telt,
    ongeacht scope/zoekfilter, zodat een actief filter geen bevindingen
    verbergt in de telling.
21. Als analist wil ik dat het Validate-rapport (Validate-knop) ongewijzigd
    blijft werken, zodat het projectbrede overzicht blijft bestaan naast de
    cel-markeringen.
22. Als analist wil ik dat de FM-editor (slice 49) zijn bestaande
    waarschuwingslabels behoudt, zodat dat werkproces niet verandert.
23. Als analist wil ik dat het laden van een project en het openen van grids
    niet merkbaar trager wordt, zodat de winst van slice 87 behouden blijft.
24. Als ontwikkelaar wil ik één overkoepelend begrip (invoerbevinding, ernst
    fout/waarschuwing) in code en documentatie, zodat gesprekken en issues
    niet per bron uiteenlopen.
25. Als ontwikkelaar wil ik de mapping bevinding → canonieke kolom declaratief
    en Qt-vrij, zodat nieuwe regels goedkoop aansluiten en testbaar zijn.
26. Als ontwikkelaar wil ik dat de ernst-semantiek in de kern (`severity` op
    het foutobject) zit en niet in de view, zodat elke afnemer (grid, rapport,
    export) dezelfde indeling ziet.

## Implementation Decisions

### Begrip en ernst (CONTEXT.md, ADR-0015)

- **Invoerbevinding** is het overkoepelende begrip; ernst is **fout** (rood,
  blokkeert opslaan/run) of **waarschuwing** (geel, nooit blokkerend).
- Het kern-foutobject (`error_obj` / `CellErrorView`) krijgt een
  `severity`-attribuut (`"error"`/`"warning"`); bestaande producenten blijven
  fouten leveren (default `"error"`, geen breaking change).
- Ernst-dualiteit per regelgroep (ADR-0015):
  - enkel-rij `validate_project`-regels → **fout** in grid;
  - kruis-entiteit `validate_project`-regels → **waarschuwing** in grid,
    **fout** bij run/Validate (onveranderd hard);
  - `validate_aannamen` → altijd **waarschuwing**.
- Run-/Validate-semantiek van `rcm_core.validators` verandert **niet**.

### Timing

- `validate_all_entities` draait bij **session-load** (project laden /
  buffer-initialisatie), zodat `edit_errors` gevuld is vóór het eerste grid
  zichtbaar wordt.
- Incrementele validatie bij `apply_rows` blijft zoals nu (per entiteit).
- **Buffer-brede hervalidatie** (incl. kruis-entiteit-waarschuwingen en
  consistentie-bevindingen) alleen bij session-load en bij de handmatige
  trigger — niet bij elke celwijziging (performance).

### Plaatsing van waarschuwingen

- Nieuw Qt-vrij adapter-module (werknaam `input_grid_findings`) bevat de
  **declaratieve mapping**: bevinding-code → entiteit + canonieke kolom per
  Input-view.
- **Fallback**: geen canonieke kolom beschikbaar of kolom verborgen → markeer
  de **sleutelkolom** van de rij; de tooltip draagt de volledige melding.
- Slice-49-bevindingen (`fm_edit_consistency`) worden hergebruikt als bron;
  de FM-editor-presentatie (labels) blijft ongewijzigd.

### Presentatie

- `EntityTableModel`: `BackgroundRole` rood (bestaand `ERROR_BACKGROUND`) voor
  fouten, geel (analoog aan de bestaande Excel-warn-kleur) voor waarschuwingen;
  rood wint. `ToolTipRole` toont alle meldingen, gegroepeerd op ernst.
- Toolbar-label van het entiteiten-grid-panel breidt de rijtelling uit met een
  bevindingen-telling per view ("N fouten, M waarschuwingen"); telt over de
  volledige view, onafhankelijk van PBS-scope/zoekfilter.
- Alle teksten via `messages`.

### Bediening

- Menubalk-item **Analyse → Controleer invoer**, action-id
  `analysis.revalidate_input`, sneltoets **F7**, niet-checkable.
- Actie is buffer-breed en ververst alle aangekoppelde grids. Geen knop per
  grid (besluit grill vraag 7: niet afleiden van de generieke workflow;
  gevorderde gebruikers bedienen via sneltoets).

### Fasering

1. **Fase 1** — severity-fundament + load-time validatie + grid-presentatie
   (rood/geel/tooltip) + hervalidatie-menu-item + telling.
2. **Fase 2** — slice-49 consistentie-bevindingen als waarschuwingen in grids.
3. **Fase 3** — `validate_project`-regels (enkel-rij als fout, kruis-entiteit
   als waarschuwing) en `validate_aannamen` in het grid.

### Grenzen

- Geen motorwijziging; geen `CACHE_INPUTS_VERSION`-bump (validatie raakt de
  JSON-vorm en het rekenresultaat niet).
- Parity-tests (`tests/test_editing_schemas_parity.py`) blijven groen.

## Testing Decisions

Goede tests toetsen **extern gedrag** aan de hoogst mogelijke seam — geen
widget-internals, geen private velden. Seams bevestigd in de sessie:

| Prioriteit | Seam | Wat wordt getest |
|------------|------|------------------|
| 1 | `rcm_core.editing.validation`/`state` (puur) | `severity` op foutobject; `edit_errors` gevuld na session-load zonder bewerking |
| 2 | `rcm_core.validators` (puur) | Regressie: run-/Validate-gedrag ongewijzigd; indeling enkel-rij vs kruis-entiteit als toetsbare metadata |
| 3 | `input_grid_findings` (adapter, Qt-vrij) | Mapping bevinding → (entiteit, rij, kolom); sleutelkolom-fallback; ernst per regelgroep |
| 4 | `EntityEditService`/`EditingSession` (pytest-qt) | `field_errors` incl. severity na load, na `apply_rows`, na buffer-brede hervalidatie |
| 5 | `EntityTableModel` (pytest-qt) | Achtergrond rood/geel, rood-wint-prioriteit; tooltip gegroepeerd per ernst |
| 6 | `workspace_menu_spec` (puur) | Nieuw Analyse-item met F7; spec-validatie (unieke shortcut) |
| 7 | Entiteiten-grid-panel (pytest-qt) | Bevindingen-telling in toolbar-label; verversing na hervalidatie |

Prior art: `tests/test_validators.py`, `tests/test_slice49_fm_editor_ux.py`,
`tests/test_desktop_faalwijzen_table_model.py`,
`tests/test_slice76_workspace_menu_spec.py`, `tests/test_slice83_entity_grid.py`.

### Wat niet testen

- Visuele kleurweergave in het venster (pure UI, conventie).
- Exacte tooltips-opmaak (alleen aanwezigheid en groepering van meldingen).
- Performance-benchmarks als harde CI-gate.

## Out of Scope

- Wijziging van de run-/Validate-semantiek van `validate_project` (ADR-0015
  legt expliciet vast dat die hard blijft).
- Automatisch zichtbaar maken van verborgen kolommen bij een bevinding
  (verworpen: onverwachte UI-sprong).
- Knop per grid of automatische buffer-brede hervalidatie na elke celwijziging
  (verworpen: workflow-afleiding resp. performance).
- Navigatie "spring naar volgende bevinding" — eventueel latere slice.
- Wijzigingen aan de FM-editor-presentatie van slice-49-bevindingen.
- Validate-venster (`--legacy-validate`) en het Validate-rapport.
- Excel-export van bevindingen.

## Further Notes

- Documentatie is al bijgewerkt tijdens de grill-sessie: `CONTEXT.md`
  (Invoerbevinding, Controleer invoer) en
  `docs/adr/ADR-0015-ernst-dualiteit-invoerbevindingen.md`.
- De waarschuwingen leven in dezelfde `edit_errors`-opslag als fouten
  (met severity), zodat `EntityEditService` één leesroute houdt; de
  blokkeer-check voor opslaan/run moet dan op `severity == "error"` filteren
  in plaats van op "is er iets in `edit_errors`".
- Let bij implementatie op het regelbudget van `results_workspace_window.py`
  (gate slice 62): menu-binding en grid-verversing in dunne helpers.
