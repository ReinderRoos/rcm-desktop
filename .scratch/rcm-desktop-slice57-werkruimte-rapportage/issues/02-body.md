## Parent

https://github.com/ReinderRoos/rcm-desktop/issues/9

## What to build

Breid rapportage uit naar A/B-vergelijking wanneer beide compare-slots gevuld zijn (slice 56-contract): KPI-tabel met kolommen A en B (slot-labels), absolute Δ op niet-beschikbaarheid % en lifecycle kosten EUR, en metadata (scenario-key, overlay-samenvatting).

Materialisatie en eligibility gebruiken `CompareSlotSnapshot` — bevroren `overlay_at_run` en labels, niet de live workspace-overlay. `ReportNarrativeService`: 2–4 zinnen feitelijke KPI-interpretatie; waarschuwing wanneer A en B verschillende scenario-keys hebben. Single-run bron-prioriteit volgens PRD (both filled → compare; anders slot A of last_run).

## Acceptance criteria

- [ ] KPI-builder ondersteunt twee scenario's + Δ-kolommen voor NB % en kosten EUR
- [ ] Compare-rapport gebruikt slot-snapshots, niet live overlay
- [ ] KPI-narrative deterministisch en zonder advieszinnen
- [ ] Waarschuwingstekst bij verschillende scenario-keys tussen A en B
- [ ] Unit-tests: compare-KPI-waarden, frozen-overlay-regressie, narrative golden
- [ ] Single-run pad uit slice 1 blijft werken

## Blocked by

https://github.com/ReinderRoos/rcm-desktop/issues/10
