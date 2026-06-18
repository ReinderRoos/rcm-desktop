# AFK-batch — referentie

## Uitvoerbaarheid

Een taak is **nu uitvoerbaar** als alle checks kloppen:

| Check | Vereist |
|-------|---------|
| Type | `AFK` in issue, of PRD-niveau zonder open grill |
| Triage | `ready-for-agent` |
| Specs | PRD + issue met acceptance criteria |
| Blockers | Geen open `Blocked by`-issues |
| Menselijk besluit | Geen open grill-vraag voor deze taak |
| HILT-voorwaarde | HILT mag **na** implementatie; blokkeert AFK niet |

**Niet uitvoerbaar → overslaan:**

- `ready-for-human`, `needs-triage`, `needs-info` → HILT of Grill
- PRD `Out of Scope` / “Later” / “Fase F” zonder child-issues → Grill
- Stub-only follow-up (bv. MC engine) zonder grill-PRD → Grill
- Alleen handcheck resterend (implementatie klaar) → HILT, geen AFK

## Queue opbouwen

1. Haal AFK-rijen uit planning-overzicht-tabel
2. Sorteer op `#`-kolom (blockers eerst)
3. Dedupe op issue-niveau (`slice NN — issue MM`)
4. Verifieer triage in bronbestand — planning kan achterlopen

```powershell
# Snelle scan open AFK-issues
rg "^\*\*Type:\*\* AFK" .scratch --glob "issues/*.md" -l
rg "^\*\*Triage:\*\* ready-for-agent" .scratch --glob "issues/*.md"
```

## TDD per taak (checklist)

```
[ ] Issue + PRD gelezen; ADR's genoteerd
[ ] Eerste tracer bullet: één gedrag, publieke API
[ ] RED bevestigd
[ ] Minimale GREEN
[ ] Volgende gedrag → herhaal
[ ] Refactor (alleen op GREEN)
[ ] pytest subset groen
[ ] Issue triage → done + outcome-regel
```

**pytest — standaard per taak:**

```powershell
python -m pytest tests/test_slice<NN>_*.py tests/test_<feature>_*.py -q --tb=short
```

Geen volledige suite. Voeg gerelateerde regressietests toe als de taak cross-cutting is.

## Context reset (~40%)

### Signalen

- Systeemmelding over context/summary
- >15 significante tool-calls sinds laatste summarize
- Meerdere slices/issues in één sessie
- Grote diffs + fixture-reads in context

### Handoff — sectie Batch-voortgang

Voeg toe aan `KANBAN_HANDOFF.md`:

```markdown
## Batch-voortgang (AFK-batch)

**Gestart:** YYYY-MM-DD
**Laatste update:** YYYY-MM-DD HH:MM

### Afgerond
| Issue | Outcome | Tests |
|-------|---------|-------|
| slice95/13 | FM delete in input grid | test_slice99_fm_delete.py — 4 passed |

### Bezig
- slice96/02 — …

### Nog in queue
- slice96/03, slice88-nav-01 (blocked: grill)

### Blockers
- MC engine: grill nodig vóór AFK
```

Na summarize: lees handoff → hervat **bezig**-taak of eerste open queue-item.

## Issue-sync na taak

In `issues/NN.md`:

```markdown
**Triage:** `done`
**Outcome:** [één regel: wat gebouwd + testbestand]
```

PRD `Status` pas op `done` zetten als **alle** child-issues done zijn.

## Blocker-escalatie

| Blocker | Batch-gedrag |
|---------|--------------|
| Ontbrekende fixture | Probeer bestaande; anders skip + noteer |
| Ratchet overschreden | Refactor naar binding; geen baseline omhoog |
| 2× testfix mislukt | Skip taak; sessie-fix in handoff |
| Grill-besluit midden in taak | Stop taak; markeer needs-triage; volgende onafhankelijke AFK |
| CI-only failure | Noteer; geen eindeloos retry |

## Eindrapport-sjabloon

```markdown
## AFK-batch — resultaat

**Periode:** …
**Afgerond:** N taken
**Overgeslagen:** M (Grill/HILT/blocker)

### Uitgevoerd
| # | Taak | Tests | Opmerking |
|---|------|-------|-----------|

### Niet uitgevoerd
| Taak | Type | Reden |

### Jouw volgende stap
[Meestal 1 HILT of 1 Grill — concreet]
```

## Anti-patterns

- Hele testklassen schrijven vóór implementatie (horizontale TDD)
- Gebruiker tussendoor om commit/goedkeuring vragen
- Volledige `pytest` zonder `-m "not perf"` filter bij routine-batch
- Grill-taken “even snel” meenemen zonder besluiten
- Context vol → stoppen zonder summarize-handoff
