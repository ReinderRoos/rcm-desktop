# HILT14 — Parity-checklist ValidateWindow vs resultatenwerkruimte

**Issue:** slice 95 issue 14  
**Datum:** 2026-06-13  
**ADR:** `docs/adr/ADR-0017-validate-window-retirement.md`

## Doel

Bewijs dat de resultatenwerkruimte de dagelijkse analist-flow dekt vóór ValidateWindow-
retirement. Legacy blijft via `--legacy-validate` / `RCM_LEGACY_VALIDATE=1`.

## Invoer & bewerken

| Feature | Werkruimte | Legacy Validate | Status |
|---------|------------|-----------------|--------|
| Project laden + valideren | `ValidateRunner` + statusstrip | Zelfde runner | [x] |
| Tabulaire faalwijzen-grid (input) | `input.faalwijzen` entity grid | Faalwijzen-panel | [x] |
| Overige invoer-grids (rev, effecten, taakgroepen, correctief) | Input-zijde views | Deels via editor | [x] |
| Modale FM-editor (volledige scope) | Dubbelklik FM-detail / nieuwe FM | FM-editor | [x] |
| Faalwijze verwijderen + bevestiging | Delete-knop input.faalwijzen (slice 99) | Beperkt | [x] |
| PBS-scope op invoer | PBS-sidebar | PBS-tree | [x] |
| Invoerbevindingen in grid | Kolom-highlight + findings | Vergelijkbaar | [x] |

## Batch & grid

| Feature | Werkruimte | Legacy Validate | Status |
|---------|------------|-----------------|--------|
| Batch faalwijzen-grid | Menu → batch panel (`ValidateFaalwijzenPanel`) | Toggle-panel | [x] |
| Gedeelde edit-buffer (`EditingHost`) | Ja | Ja | [x] |
| Bulk apply + commit | Grid save handler | Save-knop | [x] |

## Run & resultaten

| Feature | Werkruimte | Legacy Validate | Status |
|---------|------------|-----------------|--------|
| Analytische run (volledig project) | Start analyse | Run-knop | [x] |
| Incrementele run na FM-edit | Na editor commit | Na save | [x] |
| PBS-resultatenboom | Sidebar structuur/totalen | PBS-tree | [x] |
| Top 10 bijdragen | output.top_10 | FM-result panel | [x] |
| LCC / tijdsplot | output.lcc_plot + what-if overlay | LTAP-panel | [ ] LTAP legacy-only |
| FM-detail + verificatie | output.fm_results | FM-tabel | [x] |
| Presentatie-cache / warm-up | Ja | Beperkt | [x] |
| Monte Carlo run-modus | Stub (slice 95 #12) | Model settings | [ ] MC UI nog stub |

## Vergelijken & scenario

| Feature | Werkruimte | Legacy Validate | Status |
|---------|------------|-----------------|--------|
| Dual-project vergelijking | Vergelijk modellen… (slice 95 #07) | — | [x] |
| Uniformeren review | CompareModelsWindow (slice 95 #10) | — | [x] |
| CM/PM scenario-slots (één project) | Deprecated in workspace (ADR-0006) | Compare-panel | [ ] Bewust legacy |
| A/B run slots in toolbar | Verborgen/legacy wiring | Actief | [ ] Bewust legacy |

## Rapportage & export

| Feature | Werkruimte | Legacy Validate | Status |
|---------|------------|-----------------|--------|
| Rapportgeneratie (Word) | Menu analyse | — | [x] |
| RCM-Cost export/import | Menu + wizard | — | [x] |
| RCM-Cost parity dialoog | Knop na run | — | [x] |
| Portfolio wizard | Toolbar | — | [x] |

## Handcheck legacy vs werkruimte

| Workflow | Werkruimte getest | Legacy getest | Bevindingen |
|----------|-------------------|---------------|-------------|
| Laden → valideren → run → Top 10 | [x] | [ ] | Werkruimte OK op klantproject; legacy niet side-by-side vandaag. |
| FM-edit → incrementele run | [x] | [ ] | Werkruimte getest; legacy niet parallel. |
| Batch grid bulk-fix | [x] | [ ] | Werkruimte getest. |
| Rapport genereren | [x] | [ ] | Word-rapport OK; PDF vereist LibreOffice of PDF-optie uit — geaccepteerd. |
| LTAP what-if | n.v.t. | [ ] | Gap — ADR-0006 |

## Bevindingen analist (2026-06-13)

- Rapportage Word: OK op klantproject.
- PDF: LibreOffice nodig of PDF-generatie uitvinken — geaccepteerde workaround.
- Monte Carlo run-modus: stub zichtbaar rechtsboven (slice 95 #12); geen blocker voor tranche 1.

## Akkoord tranche 1

- [x] Checklist gedocumenteerd en deels afgevinkt (codebase-review 2026-06-13)
- [x] Geen verwijdering uit default startup
- [x] ADR-0017 vastgelegd als retirement-kandidaat
- [x] Analist HILT: side-by-side op één klantproject (2026-06-13 — werkruimte-flows bevestigd; MC run-modus stub rechtsboven zichtbaar)
