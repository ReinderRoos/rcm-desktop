# Architectuur — uitgestelde aanbevelingen (niet in slice 45)

Bron: `/improve-codebase-architecture` na slice 44 (2026-05-23).

**Status (2026-05-26):** Uitvoeringsroadmap grill-me → PRD slice **50** (coördinatie) + implementatie slice **46**:

- `.scratch/rcm-desktop-slice50-architectuur-roadmap-uitvoering/PRD.md` (fases 0–3, reconcile, 41-defer)
- `.scratch/rcm-desktop-slice46-fm-edit-fase2/PRD.md` (verticale AFK-tracers **issues 01–09**, milestones 46–48)

Onderstaande tabel is **historisch**; implementatie volgt de PRD/issues, niet deze checklist.

| # | Aanbeveling | Tracer-issue(s) |
|---|-------------|-----------------|
| 1 | Bundle-assemblage uit `FmEditorDialog` naar adapter | 06 |
| 2 | `apply_bundle_scope` → `EditingSession.replace_fm_scope()` | 05 |
| 3 | Eén tabulaire contract grid + editor | 01–04, 08 |
| 5 | Schema `downtime_per_failure` + nested `TimeDuration` | 05 (dict), 09 (coercion optioneel) |
| 7 | ValidateWindow ontleden (~1333 regels) | 04 (faalwijzen-panel) |
| 8 | Run-orchestratie verenigen (editor vs. `RunRunner`) | 07, 08 |
