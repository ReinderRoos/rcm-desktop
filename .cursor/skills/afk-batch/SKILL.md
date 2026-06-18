---
name: afk-batch
description: Voert alle uitvoerbare AFK-taken uit de planning automatisch uit via TDD, zonder gebruikersinterventie. Gebruikt planning-overzicht voor prioritering en summarize-chat bij contextdruk. Use when the user invokes /afk-batch, asks to run all AFK tasks, batch AFK work, or auto-implement ready-for-agent issues.
---

# AFK-batch

Voer **autonoom** alle AFK-taken uit die nu uitgevoerd kunnen worden: eerst prioriteren via `planning-overzicht`, daarna per taak `/tdd` (tracer bullets, geen horizontale slices).

## Kernregels

1. **Geen gebruikersinterventie** tussen AFK-taken — geen goedkeuring, geen `AskQuestion`, geen “wil je dat ik…?”
2. **Alleen AFK** — skip Grill en HILT; noteer ze kort in het eindrapport
3. **Geen commits/push** tenzij de gebruiker dat expliciet vroeg vóór of tijdens de batch
4. **Stop niet bij één taak** — ga door tot de AFK-queue leeg is of een harde blocker optreedt
5. **Contextbeheer** — bij ~40% contextwindow: `/summarize` (skill `summarize-chat`) en direct verder

## Wanneer starten

- Gebruiker roept `/afk-batch` aan
- “Voer alle AFK-taken uit” / “/tdd alle afk-taken die nu al kunnen”
- Na `/planning-overzicht` wanneer de gebruiker batch-uitvoering wil

## Workflow

### Fase 1 — Planning scannen

Voer de workflow uit van [planning-overzicht](../planning-overzicht/SKILL.md):

1. Scan `.scratch/*/PRD.md`, `issues/*.md`, `KANBAN_HANDOFF.md`, `HILT*.md`
2. Bouw de aanbevolen volgorde-tabel
3. Filter op **Type = AFK** met triage `ready-for-agent`
4. Pas [uitvoerbaarheidscriteria](reference.md#uitvoerbaarheid) toe — alleen taken die **nu** kunnen

Output intern (niet aan gebruiker tenzij batch klaar): genummerde AFK-queue.

### Fase 2 — Batch-lus

Voor elke taak in volgorde:

```
[ ] Context-check (~40%? → summarize → hervat)
[ ] Lees issue/PRD + relevante ADR's
[ ] /tdd: RED → GREEN → refactor (tracer bullet per gedrag)
[ ] Gerichte pytest — geen volledige suite
[ ] Update issue triage → done + korte outcome-regel
[ ] Volgende taak
```

**TDD-regels** — volg [tdd](~/.cursor/skills/tdd/SKILL.md):

- Verticale slices: één test → minimale implementatie → herhaal
- Publieke interfaces; geen implementation-detail tests
- Geen speculatieve features buiten issue-AC

### Fase 3 — Context reset (~40%)

Wanneer het contextwindow vol raakt (heuristiek: lange sessie, veel diffs/fixtures, samenvattingswaarschuwing, of expliciet ~40%):

1. Voer **summarize-chat** uit → update `KANBAN_HANDOFF.md` in actieve slice-map
2. Schrijf **Batch-voortgang** in handoff:
   - Afgeronde AFK-taken (issue → commit/teststatus)
   - Huidige taak + wat nog open is
   - Blockers
3. **Hervat direct** — lees handoff + PRD/issues; ga verder waar je stopte
4. Vraag de gebruiker **niet** om bevestiging

### Fase 4 — Afronding

Lever één compact rapport:

| # | Taak | Status | Tests |
|---|------|--------|-------|
| … | Slice XX issue NN | done / blocked | `pytest …` |

Plus:
- **Overgeslagen** — Grill/HILT met reden
- **Blockers** — wat menselijke beslissing of HILT vereist
- **Volgende aanbevolen actie voor gebruiker** — meestal HILT of Grill

## Stoppen vs doorgaan

| Situatie | Actie |
|----------|-------|
| AFK klaar, tests groen | Volgende taak |
| Geen AFK meer in queue | Afronden met rapport |
| Issue `Blocked by` nog open | Skip; noteer blocker |
| Triage `needs-triage` / geen specs | Skip → Grill |
| Test faalt na 2 gerichte fix-pogingen | Noteer blocker; volgende AFK (tenzij keten-afhankelijk) |
| Architectuurbesluit nodig | Stop die taak; noteer als Grill; ga verder met onafhankelijke AFK |
| Gebruiker vroeg expliciet om commit | Commit per taak of aan batch-einde — volg git-regels |

## rcm-desktop conventies

- Adapter test-first (`pytest`, `pytest-qt`); views niet test-gestuurd tenzij issue dat vraagt
- Geen `rcm_core`-imports in `views/` (runtime)
- Ratchet-tests (`test_slice62_panel_gate`) — extractie naar binding-modules i.p.v. baseline verhogen
- Fixtures onder `tests/fixtures/`; geen volledige suite draaien tenzij issue/CI dat vereist

## Gerelateerde skills

| Skill | Wanneer |
|-------|---------|
| [planning-overzicht](../planning-overzicht/SKILL.md) | Fase 1 — prioritering |
| [tdd](~/.cursor/skills/tdd/SKILL.md) | Fase 2 — implementatie |
| [summarize-chat](../summarize-chat/SKILL.md) | Context reset ~40% |
| [to-issues](~/.cursor/skills/to-issues/SKILL.md) | Alleen als batch Grill-taken ontdekt zonder issues |

## Extra details

- Uitvoerbaarheid, pytest-commando's, handoff-sjabloon: [reference.md](reference.md)
