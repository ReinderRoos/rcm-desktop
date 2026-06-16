---
name: planning-overzicht
description: Analyseert rcm-desktop planning en geeft een overzicht van ingeplande taken met onderscheid tussen HILT, AFK en grill. Use when the user asks for a planning overview, roadmap status, next steps, or what still needs grilling, HILT, or AFK work.
---

# Planning-overzicht

Geef een **actueel planningsoverzicht** van het rcm-desktop-project: wat is gepland, wat is klaar, wat moet nog — met duidelijk onderscheid tussen **AFK**, **HILT** en **Grill**.

## Wanneer uitvoeren

- Gebruiker vraagt om planning, roadmap, volgende stappen, of status van slices
- Na afronding van een slice: wat is de aanbevolen volgorde verder?
- Vóór `/tdd` of `/to-issues`: welke taken zijn al specificeerbaar?

## Taaktypen

| Type | Betekenis | Wie doet het |
|------|-----------|--------------|
| **AFK** | Volledig gespecificeerd; agent kan implementeren/testen zonder menselijke besluiten | Agent (`/tdd`, `ready-for-agent`) |
| **HILT** | Handmatige check door analist: visuele QA, echte klantprojecten, parity-bewijs | Gebruiker (analist/product owner) |
| **Grill** | Principiële product-/architectuurbesluiten ontbreken; eerst `/grill-with-docs` | Gebruiker + agent in interview |

**Classificatieregels:**

1. Issue met `**Type:** AFK` en triage `ready-for-agent` → **AFK**
2. Issue/PRD met open HILT-checklist, `HILT`-verwijzing in AC, of `ready-for-human` voor handcheck → **HILT**
3. Geen PRD, PRD zonder grill-besluiten, epic in `Out of Scope` zonder PRD, of expliciet “follow-up grill” → **Grill**
4. PRD `done` + alle issues `done` → **niet opnemen** als open taak (wel vermelden onder “Afgerond”)

## Workflow

1. **Scope bepalen** — hele repo of één slice/feature (uit gebruikersvraag)
2. **Bronnen scannen** (parallel waar mogelijk):
   - `.scratch/*/PRD.md` — `Status`, `Triage`, fase/volgorde
   - `.scratch/*/issues/*.md` — triage, `Type`, acceptance criteria, `Blocked by`
   - `.scratch/*/KANBAN_HANDOFF.md` — “Volgende kaarten”, sessie-status
   - `.scratch/*/HILT*.md` — open vs afgevinkte handchecks
   - `docs/adr/` — geplande maar nog niet geïmplementeerde ADR's
   - `AGENTS.md`, `CONTEXT.md` — architectuurconstraints
   - Optioneel: `git log`, open PR, huidige branch
3. **Open taken verzamelen** — alleen items die **niet** `done` / `wontfix` zijn
4. **Typiseren** — per taak AFK, HILT of Grill toekennen
5. **Ordenen** — aanbevolen uitvoervolgorde:
   - Blockers en `Blocked by`-ketens eerst
   - PRD-volgorde en fase (A→B→C…) respecteren
   - HILT direct vóór of na bijbehorende AFK-merge (checklist vóór merge)
   - Grill vóór PRD/issues van die epic
6. **Output schrijven** — zie template hieronder
7. **Kort samenvatten** — 2–3 zinnen: waar staan we, wat is de eerstvolgende actie voor de gebruiker

## Output-template

### 1. Samenvatting (2–3 zinnen)

Huidige stand + duidelijkste volgende stap voor de gebruiker.

### 2. Aanbevolen volgorde (hoofdtabel)

Gebruik **altijd** deze kolommen:

| # | Taak | Type | Jouw rol | Wat gebeurt er |
|---|------|------|----------|----------------|
| 1 | Slice XX — korte titel | AFK / HILT / Grill | … | … |

**Kolom “Jouw rol”** — in eenvoudig Nederlands, tweede persoon:

| Type | Voorbeelden “Jouw rol” |
|------|------------------------|
| AFK | “Start de agent (`/tdd slice XX`)” · “Optioneel: PR reviewen na merge” |
| HILT | “Handmatig testen in de app met [fixture/klantproject]” · “Checklist invullen en afvinken” · “Bevestigen dat gedrag klopt vóór merge” |
| Grill | “Besluiten nemen in `/grill-with-docs`-sessie” · “Keuze maken tussen opties; agent volgt aanbeveling tenzij je anders kiest” |

**Kolom “Wat gebeurt er”** — één zin, geen jargon, wat de stap oplevert voor de analist of het product:

- Goed: “Twee projectbestanden naast elkaar vergelijken per faalwijze.”
- Slecht: “CompareSession + balanced presentation DTO.”

### 3. Per type (compact)

Drie korte bullet-lijsten — alleen **open** items:

- **Grill** — wat eerst besloten moet worden
- **AFK** — wat de agent kan pakken
- **HILT** — waar jij in de app moet kijken

### 4. Afgerond (optioneel, max 5 regels)

Recent afgeronde slices/epics — alleen ter context, geen volledige historie.

### 5. Bronverwijzing

Pad naar PRD/issues/checklists per genoemde taak.

## rcm-desktop conventies

- Slice-docs: `.scratch/rcm-desktop-slice<N>-<slug>/`
- Triage-labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `done`, `wontfix`
- Issue `Type:` veld: meestal `AFK`; HILT staat vaak in acceptance criteria of aparte `HILT*.md`
- Strategische roadmap: slice 95 PRD — fases A–F; latere epics (portfolio, bibliotheek, MC volledig) staan in Out of Scope tot grill + PRD
- Lees vóór ordenen de **Voorgestelde slice-volgorde** in de meest recente roadmap-PRD

## Kwaliteitsregels

- **Geen verzonnen taken** — elke rij moet traceerbaar zijn naar een bestand
- **Geen dubbele rijen** — issue-niveau als er issues zijn; anders PRD-niveau
- **Eerlijk over onzekerheid** — “status onduidelijk; triage nodig” i.p.v. gokken
- **Proportioneel** — bij slice-specifieke vraag geen volledige repo-historie
- **Geen commit/push** tenzij gebruiker vraagt

## Voorbeeld (ingekort)

| # | Taak | Type | Jouw rol | Wat gebeurt er |
|---|------|------|----------|----------------|
| 1 | Slice 96 — MC engine v1 | Grill | Besluiten nemen over seed, parallelisatie en resultaatopslag | Monte Carlo wordt een echte rekenworkflow i.p.v. alleen een UI-stub |
| 2 | Slice 96 — MC engine v1 | AFK | Start `/tdd slice 96` na grill | Simulaties draaien en resultaten tonen in de werkruimte |
| 3 | Slice 96 — MC HILT | HILT | Run op demo-project; bevestig dat voortgang en annuleren kloppen | Zeker weten dat MC in de praktijk bruikbaar is |

## Extra bronnen

- Classificatie- en scan-details: [reference.md](reference.md)
