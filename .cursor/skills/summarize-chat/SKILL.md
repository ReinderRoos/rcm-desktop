---
name: summarize-chat
description: Summarizes agent chat sessions into structured handoff documents for rcm-desktop slice work. Use when the user asks to summarize the chat, create a session handoff, update KANBAN_HANDOFF.md, or prepare context for a follow-up session.
---

# Summarize Chat

Produce a **handoff document** another agent (or human) can use cold — without re-reading the full chat.

## When to run

- User asks to summarize chat, wrap up session, or write handoff
- Slice/issue work is pausing mid-stream
- Significant bugs were fixed outside issue text (sessie-fixes)

## Workflow

1. **Identify scope** — slice folder (`.scratch/<slice>/`), issues touched, ADRs referenced
2. **Extract facts only** — decisions, file paths, test commands, counts/metrics, open gaps
3. **Skip noise** — no play-by-play of failed attempts unless the failure explains a constraint
4. **Update or create** — prefer updating existing `KANBAN_HANDOFF.md` in the slice folder; create only if missing
5. **Sync issue triage** — update `issues/NN.md` triage + one-line outcome when an issue moved state
6. **Verify** — mention pytest subset actually run (with pass/fail), not hypothetical

## Required sections

Use [handoff-template.md](handoff-template.md). Minimum bar:

| Section | Content |
|---------|---------|
| Kanban-status | Issue table with triage + short opmerking |
| Wat werkt | Verified flows + fixture paths |
| Sessie-fixes | Bugs fixed outside issue text (symptom → cause → fix → test) |
| Architectuur | Only if modules/pipeline changed |
| Bekend gedrag | Acceptable warnings, intentional gaps |
| Volgende kaarten | Ordered, actionable |
| Belangrijkste bestanden | Path → rol table |

## rcm-desktop conventions

- Slice docs live under `.scratch/<feature>/` (PRD, issues/, KANBAN_HANDOFF.md)
- Read `AGENTS.md` + slice `PRD.md` before rewriting handoff
- Issue triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `done`, `wontfix`
- Test commands: run from repo root with `.\.venv\Scripts\python.exe -m pytest ...`
- Do **not** commit unless user asks

## Quality bar

**Good opmerking (issue row):**
> `PM_SEMANTICS_SPIKE.md`; CM: 54 PM-links / 15 waarschuwingen; `Enabled` = scenario, niet koppeling

**Bad opmerking:**
> worked on PM stuff

**Good sessie-fix:**
> **Symptoom:** 65× `PBS_EFFECTIVE_BOUWJAAR_ZERO` → **Fix:** `propagate_bouwjaar_to_ancestors()` → **Test:** `test_cm_fixture_import_valid_after_wizard_choices`

## Output

1. Updated `KANBAN_HANDOFF.md` (or new file in slice folder)
2. Brief user-facing summary: what changed, what's open, suggested next step
