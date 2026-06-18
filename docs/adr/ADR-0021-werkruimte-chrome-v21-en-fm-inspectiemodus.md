# ADR-0021: Werkruimte chrome v2.1 + FM-inspectiemodus

**Status:** accepted  
**Date:** 2026-06-18  
**Parent:** HILT107 grill (post slice 107); amends ADR-0020

## Context

Slice 107 (ADR-0020) leverde navigatierail + chrome-footer. HILT107 toonde:

- View-label «Top bijdragen» te klein en op de verkeerde plek (footer links).
- Input-rail-labels te kort/klein.
- FM-inspector moet validatie ondersteunen met LCC-plot per faalwijze, niet
  alleen een jaartabel.
- Dubbelklik-gedrag verwarrend: editor op Output, geen editor op Input.

ADR-0020 plaatste view-context in footer-zone links. Analisten willen oriëntatie
**boven** de inhoud; footer blijft puur bediening.

## Decision

### Chrome-layout v2.1 (amends ADR-0020 §footer + rail)

**View-titel** — Prominente kopregel direct boven `detail_zone` met het
volledige view-label uit de registry. Overlay-status (what-if actief, enz.)
**niet** in de titel; blijft in chrome-footer of statusstrip.

**Werkruimte-chrome-footer** — Twee zones (ADR-0020 zone links vervalt):

| Zone | Inhoud |
|------|--------|
| Midden | Gedeelde chrome (metric, horizon, NB, what-if-knoppen, overlay-status) |
| Rechts | ~120px; LCC-maatregeltypes verticaal; leeg indien niet van toepassing |

**Navigatierail** — Breedte ~160px (was ~144px). Groter lettertype voor
view-tabs. **Output:** rail-labels KPI, LCC, LTAP, TopX. **Input:**
bedieningslabels Faalwijzen, REV, Effect, Taakgroep, Correctief (formele
view-labels blijven in Beeld-menu en view-titel).

### Top bijdragen — diagram + inspectiemodus

**Top bijdragen-diagram** — Bestaand Top-N staafdiagram (ranking op actieve
metric). Blijft naast tabelweergave via toggle.

**FM-inspectiemodus** — Alleen in **tabelweergave**:

- Openen: **dubbelklik** op rij (enkele selectie opent inspector niet).
- Tabel: **contextvenster** max. 3 rijen (boven · geselecteerd · onder);
  randen zonder placeholders; 1–2 rijen totaal → toon alle beschikbare.
- Onder tabel: lifecycle-samenvatting, reconcile, **LCC-plot op faalwijze-niveau**
  gekoppeld aan dezelfde filters als hoofdtabel:
  - faalmomenten / NB: enkelvoudige reeks per kalenderjaar;
  - kosten: CM + PM gestapeld per jaar (PM-serie in adapter).
- **Sluiten:** volledige gefilterde tabel terug.
- **Pijl omhoog/omlaag:** vorige/volgende FM in gefilterde lijst.
- **Bewerken…:** opent faalwijze-editor (bewuste stap na validatie).
- Schakelen naar diagram: inspectiemodus sluit automatisch.

### Faalwijze-editor — ingangen

| Pad | Actie |
|-----|--------|
| Input → Faalwijzen | Dubbelklik → editor (slice 109) |
| Top bijdragen → FM-inspector | Knop Bewerken… → editor |
| Top bijdragen dubbelklik | Inspectiemodus only (geen directe editor) |

Overige Input-views: dubbelklik→editor wanneer entity-editors bestaan; tot
dan grid-only.

## Alternatives considered

| Optie | Reden afgewezen |
|-------|-----------------|
| Footer-context behouden | HILT: te klein, concurreert met filters |
| Enkele selectie opent inspector | Botst met tabel-navigatie; dubbelklik explicieter |
| 3 rijen met placeholders aan rand | Voelt als kapotte data |
| Diagram-knop disabled bij inspector | Extra state; sluiten bij toggle eenvoudiger |
| Kosten alleen CM in inspector | Verbergt PM-bijdrage; lifecycle toont CM+PM |
| Dubbelklik Top bijdragen → editor | Analyse vs bewerken vermengd; Input primair |

## Consequences

- ADR-0020: footer drie zones → twee zones; view-context verplaatst naar
  view-titel; rail ~160px; Input bedieningslabels.
- `CONTEXT.md`: View-titel, Top bijdragen-diagram, FM-inspectiemodus,
  Faalwijze-editor openen (Input).
- Implementatie in vertical slices: **107-B** (layout) → **108** (inspector +
  plot) → **109** (Input dubbelklik editor, Top bijdragen editor weg).
- Verwijderen/vervangen: `fm_inspector_year_table_view` als primaire viz;
  `selectionChanged` → inspector wiring; Top bijdragen `doubleClicked` → editor.
- Tests: inspectiemodus state, 3-rijen-filter, metric→plot, diagram sluit
  inspector, Input dubbelklik editor.

## References

- ADR-0020 — chrome-layout v2 (deels superseded voor footer + rail)
- ADR-0019 — presentatielaag v1
- Slice 34 — FM-verificatie service
- Slice 104 — Top bijdragen single-run diagram
- HILT107 grill transcript (2026-06-18)
