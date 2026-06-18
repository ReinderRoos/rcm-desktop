# Planning-overzicht — referentie

## Scan-commando's

Vanuit repo-root (PowerShell):

```powershell
# PRD-status per slice
Get-ChildItem .scratch -Filter PRD.md -Recurse | ForEach-Object { $_.DirectoryName; Select-String -Path $_.FullName -Pattern 'Status|Triage' -SimpleMatch | Select-Object -First 3 }

# Open issues (niet done)
rg -l "^\*\*Triage:\*\* (ready-for-agent|ready-for-human|needs-triage|needs-info)" .scratch --glob "issues/*.md"

# HILT-checklists
Get-ChildItem .scratch -Filter "HILT*.md" -Recurse

# KANBAN handoffs met volgende stappen
rg "Volgende kaarten|volgende stap" .scratch -i --glob "KANBAN_HANDOFF.md"
```

## Bronprioriteit

Bij conflicterende status tussen bronnen:

1. Issue `**Triage:**` + afgevinkte acceptance criteria
2. `KANBAN_HANDOFF.md` (meest actuele sessie)
3. PRD `Status` / `Triage`
4. HILT-checklist (open `[ ]` vs `[x]`)

## AFK vs HILT vs Grill — edge cases

| Signaal | Classificatie |
|---------|---------------|
| `Type: AFK` + triage `ready-for-agent` | AFK |
| AFK-issue met “HILT: handcheck vóór merge” in AC, implementatie al klaar | HILT (aparte rij) |
| `ready-for-human` zonder specs | HILT of Grill — lees issue-body |
| PRD “Out of Scope” / “Later” / “Fase F” | Grill (tenzij child-PRD bestaat) |
| Stub UI (bv. MC run-modus zonder engine) | Grill voor volgende fase; HILT alleen voor huidige stub |
| `needs-triage` op nieuw bugreport | Grill of triage eerst |

## Ordeningsheuristieken

1. **Blockers** — `Blocked by` in issues; dependency-grafiek topologisch sorteren
2. **Roadmap-fase** — slice 95 PRD fases A→F; daarna epics uit Out of Scope
3. **Stabiliteit vóór features** — bugfixes en seams vóór nieuwe workflows
4. **HILT-koppeling** — HILT-rij direct na de AFK-rij waarvan het de handcheck is
5. **Paralleliseerbaar** — vermeld in samenvatting als AFK-taken geen `Blocked by` delen

## Jouw rol — formuleringen

Gebruik deze sjablonen (pas `[…]` aan):

**AFK**
- “Start de agent: `/tdd [slice/issue]`”
- “Geen actie nodig; agent implementeert en test”
- “Optioneel: PR reviewen als [slice] klaar is”

**HILT**
- “Open de app en doorloop [checklist-pad] met [project/fixture]”
- “Bevestig dat [gedrag] klopt; vink checklist af of meld afwijkingen”
- “Vergelijk side-by-side: legacy vs werkruimte (parity)”

**Grill**
- “Plan een `/grill-with-docs`-sessie over [onderwerp]”
- “Kies uit de voorgestelde opties (agent adviseert [X])”
- “Bevestig scope vóór PRD/issues worden aangemaakt”

## Wat gebeurt er — voorbeelden per domein

| Domein | Voorbeeldzin |
|--------|--------------|
| Input-grid | “Invoertabellen filteren op PBS-boom en zoektekst.” |
| Invoerbevindingen | “Fouten en waarschuwingen zichtbaar in de invoertabellen.” |
| Vergelijken | “Twee modellen naast elkaar vergelijken per faalwijze.” |
| Uniformeren | “Verschillen reviewen en goedgekeurde wijzigingen toepassen.” |
| Monte Carlo | “Onzekerheid in resultaten via simulaties.” |
| ValidateWindow | “Oude validate-flow uitfaseren; alles via de werkruimte.” |
| Architectuur | “UI-logica uit het hoofdvenster halen; minder regressies.” |

## Bekende roadmap-ankers (rcm-desktop)

Ter orientatie — **altijd opnieuw verifiëren** via `.scratch/`:

| Bereik | Typische status (2026-06) |
|--------|---------------------------|
| Slices 87–94 | Meestal `done` (input-grid, bevindingen, dirty-seam, edit-unificatie, UX hotfixes) |
| Slice 95 | Issues 01–14 `done`; MC is stub; ValidateWindow nog niet verwijderd |
| Slice 96+ | MC volledig, portfolio, bibliotheek — grill + PRD nodig |
| Slice 88 follow-up | “Navigatie naar volgende bevinding” — Out of Scope tot grill |

## Gerelateerde skills

- `/grill-with-docs` — vóór Grill-taken
- `/to-prd` — na grill-besluiten
- `/to-issues` — PRD → tracer bullets
- `/tdd` — AFK-implementatie
- `summarize-chat` — sessie-handoff bij pauze
