# ADR-0019: RCM2 presentatielaag v1

**Status:** accepted  
**Date:** 2026-06-16  
**Parent:** slice 102 PRD — RCM2 presentatielaag v1 (grill-with-docs 2026-06-16)

## Context

Slice 100/101 leverden scenariovergelijking en MC-presentatie-pariteit, maar de
resultatenwerkruimte mist Delta Pi-huisstijl, spec-conforme layout-shell en
Faalwijze-analyse-interacties (FM compare). Styling is verspreid over ad hoc
`setStyleSheet`-calls. De RCM2 UI-spec definieert tokens, topbar, StatusStrip,
footer en compare-presentatieregels.

ADR-0007 regelt scenariovergelijking functioneel; deze ADR regelt **presentatie**
en tranche-indeling.

## Decision

### Thema-aanpak (102-A)

- **Centraal Qt-thema:** `rcm_desktop/theme/` met producttokens (`DP_NAVY`,
  `DP_SCENARIO_1`, `DP_SCENARIO_2`, …) en één QSS via `apply_rcm2_theme(app)`.
- **Dekking:** hele `ResultsWorkspaceWindow` (Input- én Output-views). ValidateWindow
  blijft buiten scope tot slice 99 (ADR-0017).
- **Typografie:** Calibri Light / Calibri met Segoe UI-fallback; geen font-bundles v1.
- **Layout-shell:** App-wordmark (tekst v1), bestaande QMenuBar blijft, StatusStrip
  (persistent validatie/MC), Werkruimte-footer (`QStatusBar`, transient meldingen).
- **KPI-overzicht:** gethemed; **standaard ingeklapt** in alle modi (Beeld-menu).
- **Scenario-kleur:** scenario 1 = `#E6332A`, scenario 2 = `#A3195B` op compare-kolomkoppen
  en chart-series in Top 10, LCC en FM.

### Tranche-structuur

| Tranche | Inhoud |
|---------|--------|
| **102-A** | Reskin + shell + scenario-kleuren |
| **102-B1** | Faalwijze-analyse tabelregels |
| **102-B2** | Tabel↔diagram-weergave |

HILT-checkpoints na A, B1 en B2.

### Faalwijze-analyse (102-B) — grenzen v1

Geen aparte view in de view-registry; hergebruik FM-output + compare-chrome.

| Regel | Besluit |
|-------|---------|
| Metric-gestuurde kolomkeuze | Alleen id + naam + actieve metriek per scenario-kolom |
| NMF/RF | Toggle, default uit |
| Rij-uitlijning | Unie S1 ∪ S2; sort op S1-waarde actieve metriek |
| Highlight | `\|S1−S2\|/S1 > 20%` wanneer S1>0 en beide waarden aanwezig |
| Kolomfilters | Geen in compare; PBS-scope volstaat |
| FM-inspector | Niet beschikbaar tijdens scenariovergelijking |
| Diagram | Exclusieve tabel↔diagram-switch; gepaarde horizontale balken |

Adapter levert gedeeld aligned-row DTO voor tabel én diagram. Rekeneenheden en
bestaande adapter-DTO's blijven leidend; geen parallel mock-datamodel.

## Alternatives considered

| Optie | Reden afgewezen |
|-------|-----------------|
| Per-widget `setStyleSheet` | Fragmentatie; moeilijk HILT-pariteit |
| Alleen shell, geen compare-kleuren in Top 10/LCC | Wijkt af van UI-spec en grill-besluit |
| FM-inspector in compare v1 | Mixed-slot complexiteit; compare = vergelijken, niet inspecteren |
| Symmetrische highlight `max(S1,S2)` | Wijkt af van UI-spec |

## Consequences

- Nieuwe presentatiecode in `theme/` + view/orchestrator; views geen runtime
  `rcm_core`-imports.
- ADR-0007 blijft functionele bron voor scenariovergelijking; ADR-0019 is
  presentatie-companion.
- Glossary-termen in `CONTEXT.md` (RCM2 presentatielaag, Faalwijze-analyse, …)
  zijn producttaal; implementatiedetails leven hier en in slice-issues.

## References

- ADR-0007 — workspace scenariovergelijking
- ADR-0017 — ValidateWindow retirement
- `.scratch/rcm-desktop-slice102-rcm2-presentatielaag/PRD.md`
