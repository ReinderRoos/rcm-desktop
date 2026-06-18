# ADR-0014 — Input entiteiten-grid: PBS-scope + zoekbalk i.p.v. per-kolom filterrij

## Status

Accepted (2026-06-11).

## Datum

2026-06-11

## Context

Slice 81 introduceerde een herbruikbare **tabel-filterrij** (per kolom, EN-combinatie,
bool/numeric expressies) met FM-resultaten als eerste afnemer. Slice 83 plante het
**entiteiten-grid** als tweede afnemer. In de praktijk laden Input-vensters traag:
de volledige filterrij creëert N Qt-widgets per kolom, en `EntityEditService.rows()`
herberekent op elke cel- en filter-pass.

Voor grote modellen is **PBS-scope** (subtree-selectie in de werkruimte-boom) de
natuurlijke navigatie — analisten focussen al op een onderdeel via dezelfde boom
als Output. Per-kolom filters op Input leveren weinig extra waarde t.o.v. die scope
plus een globale zoekbalk.

## Beslissing

### Input-filter ≠ Output-filter

| Zijde | Filter-UI |
|-------|-----------|
| **Output** (FM-resultaten) | Volledige **tabel-filterrij** (slice 81) |
| **Input** (entiteiten-grid) | **PBS-scope** (waar van toepassing) + **globale zoekbalk** per view |

Geen per-kolom filterrij, geen domein-comboboxes op Input (Faalwijzen-batch-grid
in ValidateFaalwijzenPanel blijft ongewijzigd).

### PBS-scope op Input

- Hergebruik `workspace_state.scope_id` en `collect_pbs_subtree_ids` — zelfde
  presentatie-filter als Output, geen deelrun.
- **PBS-gebonden views:** Faalwijzen, REV-taken (via `fm_id` → faalwijze.`pbs_id`),
  Correctief (via `pbs_id`).
- **Niet PBS-gebonden:** Effecten, Taakgroepen tonen altijd het volledige project;
  bij actieve scope: subtiele statusregel “PBS-scope niet van toepassing”.
- Filtering op **proxy-niveau**; `edit_current`-buffer blijft ongewijzigd.

### Performance in dezelfde slice

- Cache `EntityEditService.rows()`; invalideren bij wijzigingen.
- Kolomkeuze zonder volledige `attach()` (`setColumnHidden` + lichte sync).
- Lazy attach: **niet** in deze slice (aparte follow-up).

### Grens

De seam `table_filter_parser` + `TableColumnFilterProxy` blijft bestaan voor
Output en eventuele toekomstige grote analyse-tabellen. Niet opnieuw op Input
plannen zonder dit ADR te herzien.

## Gevolgen

- `entity_grid_filter_binding` en `TableFilterRowWidget` verdwijnen uit Input-pad.
- Nieuwe Qt-vrije scope-policy + Input-filter-proxy (patroon: `FaalwijzenFilterProxy`).
- `CONTEXT.md`: termen *Tabel-filterrij*, *Entiteiten-grid*, *PBS-scope op Input*.
- Geen `CACHE_INPUTS_VERSION`-bump; geen `rcm_core`-wijziging vereist.

## Overwogen alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Volledige filterrij behouden + alleen cache | Widget-footprint en filter-pass-kosten blijven |
| Alleen globale zoekbalk, geen PBS-scope op Input | Mist de hoofd-navigatie voor grote modellen |
| PBS-scope op alle vijf views incl. Taakgroepen via PM-referenties | Taakgroepen zijn projectbreed gedeeld; regels worden onduidelijk |
