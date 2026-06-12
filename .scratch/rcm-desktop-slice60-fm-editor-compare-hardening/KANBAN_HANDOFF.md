# Kanban-handoff — slice 60 FM-editor + compare hardening

**PRD:** `PRD.md`  
**Triage:** `ready-for-agent` (alle issues)  
**Bron:** grill-me 2026-06-04 (vier punten, aanbevelingen gevolgd)

## Volgorde

1. `issues/01.md` — REV + incrementele fout + motor  
2. `issues/02.md` — auto-seed slot A, seed-knoppen weg  
3. `issues/03.md` — taakgroep-dialoog  
4. `issues/04.md` — PM-taak-dialoog  

## Test seams (PRD)

- `FmEditCommitService` + `fm_edit_consistency` (hoog)  
- `run_incremental_analysis` / motor REV+non-aging (kern)  
- Compare slot auto-seed (werkruimte smoke)  
- `TaskGroupDraftService`, `PmTaskDraftService` (adapter unit)  

## GitHub

`gh` niet op setup-machine — issues lokaal. Optioneel handmatig parent issue op `ReinderRoos/rcm-desktop` aanmaken met link naar deze map.
