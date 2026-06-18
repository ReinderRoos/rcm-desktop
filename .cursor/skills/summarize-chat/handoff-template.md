# Kanban-handoff — [slice name] ([YYYY-MM-DD])

**Doel:** Vastlegging voor een schone vervolgsessie. Lees dit bestand + `PRD.md` vóór je het kanban-bord oppakt.

**Repo:** `rcm-desktop`  
**Slice-map:** `.scratch/<slice-folder>/`  
**ADR:** `[path if relevant]`  
**Domein:** `CONTEXT.md` ([sectie if relevant])

---

## Kanban-status (issues)

| # | Titel | Triage | Opmerking |
|---|--------|--------|-----------|
| NN | … | **done** / **needs-info** / … | `[bestand]`; `[metric]`; `[besluit in ≤15 woorden]` |

**Slice status:** [tracer-bullet af / in progress]. **Open productwerk:** [bullets]

---

## Wat werkt (geverifieerd)

### [Flow name]

1. …

### Fixtures (tests)

| Bestand | Gebruik |
|---------|---------|
| `tests/fixtures/…` | … |

### Tests (relevante subset)

```powershell
cd rcm-desktop
.\.venv\Scripts\Activate.ps1
python -m pytest [paths] -q
```

---

## Sessie-fixes (buiten issue-tekst)

### N. [Korte titel]

- **Symptoom:** …
- **Oorzaak:** …
- **Fix:** `[file]` — …
- **Test:** `[test path]`

---

## Architectuur (kort)

```
[alleen bij pipeline-wijziging]
```

**Regels:** UI → alleen via `rcm_desktop/adapter/`; …

---

## Bekend gedrag / acceptabel voorlopig

- …

---

## Aanbevolen volgende kanban-kaarten

1. …

---

## Belangrijkste bestanden (wijzigingen)

| Pad | Rol |
|-----|-----|
| … | … |

---

## Grill-me / productbesluiten (indien nieuw)

- …

---

*Laatst bijgewerkt: [YYYY-MM-DD] — [één regel wat er gebeurde].*
