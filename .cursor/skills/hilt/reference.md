# HILT — referentie

## Checklist-bronnen (rcm-desktop)

| Checklist | Pad | Issue |
|-----------|-----|-------|
| Vergelijkingswerkruimte | `.scratch/rcm-desktop-slice95-strategic-roadmap-juni2026/HILT07_HANDCHECK.md` | slice 95 #07 |
| ValidateWindow parity | `.scratch/rcm-desktop-slice95-strategic-roadmap-juni2026/HILT14_PARITY_CHECKLIST.md` | slice 95 #14 |
| Meekoppel parent-rollup | `.scratch/rcm-desktop-slice55-meekoppel-discovery-parent-rollup/KANBAN_HANDOFF.md` | slice 55 #04 |
| Meekoppel preview-inzicht | `.scratch/rcm-desktop-slice54-meekoppel-workflow-seam/HANDCHECK-preview-insight.md` | slice 54 #03g |
| Meekoppel gate 2a→2b | `.scratch/rcm-desktop-slice39-meekoppelkansen-planning-2a/KANBAN_HANDOFF.md` | slice 39 |

Zoek open HILT:

```powershell
rg -l "HILT|handcheck|HANDCHECK|ready-for-human" .scratch --glob "*.md" -i
rg "\[ \]" .scratch --glob "HILT*.md"
```

## AskQuestion-sjablonen

### Zichtbaarheid / werking

```
prompt: "Zie je [element] zoals verwacht?"
options:
  - id: ok — "Ja, klopt"
  - id: fail — "Nee, klopt niet (ik licht toe)"
  - id: unsure — "Twijfel — ik stuur screenshot of toelichting"
  - id: other — "Anders / aanvullingen"
```

### GO/NO-GO (eindstap)

```
prompt: "Wat is je oordeel voor deze handcheck?"
options:
  - id: go — "GO — akkoord"
  - id: go-gap — "GO met kanttekening"
  - id: nogo — "NO-GO — blocking probleem"
  - id: pause — "Later verder"
```

### Parity-vergelijking (legacy vs werkruimte)

```
prompt: "Gedraagt de werkruimte zich hetzelfde als legacy voor [feature]?"
options:
  - id: parity — "Ja, parity OK"
  - id: gap — "Werkruimte mist iets"
  - id: better — "Werkruimte is beter (geen gap)"
  - id: untested — "Nog niet getest"
```

### Getal / telling

Geen meerkeuze — vraag expliciet:

> "Hoeveel [locatierijen / diffs / fouten] zie je? Typ het getal of stuur een screenshot."

## Stap ontleden uit checklist

Lange checklist-regels splitsen:

| Origineel | Stappen |
|-----------|---------|
| "Start app + open menu + kies bestanden" | 3 stappen |
| Sub-bullet met 2 checks | 1 stap + 1 vraag met meerkeuze per check, of 2 stappen |
| "Herhaal met project B" | Aparte stap met fixture-keuze |

## Notities vastleggen

Bij GO, update bronbestand:

```markdown
| Project A | Project B | Bevindingen |
|-----------|-----------|-------------|
| … | … | [datum] — [korte conclusie] |

## Akkoord
- [x] Analist akkoord — [issue] kan op `done`
```

## Relatie andere skills

| Skill | Wanneer |
|-------|---------|
| `planning-overzicht` | Welke HILT-taken open staan |
| `summarize-chat` | Sessie pauzeren → handoff |
| `qa` | Bug registreren na NO-GO |
| `triage` | Issue op `done` zetten na GO |

## Veelvoorkomende valkuilen

| Valkuil | Vermijden |
|---------|-----------|
| Hele checklist plakken | Max 3 bullets actie + 1 vraag |
| Code fixen tijdens HILT | Alleen noteren; fix = aparte taag |
| GO zonder laatste stap | Altijd expliciet GO/NO-GO vragen |
| Meerdere vragen | Splits in aparte beurten |
