---
name: hilt
description: Begeleidt de gebruiker stap voor stap door HILT-handchecks met een concrete checklist, één vraag per stap en meerkeuze waar mogelijk. Use when the user invokes /hilt, asks for a handcheck, manual QA, HILT checklist, or needs to validate something in the app themselves.
---

# HILT

Begeleid de gebruiker **interactief** door taken die alleen een mens kan uitvoeren en valideren (visuele QA, klantprojecten, parity-bewijs, GO/NO-GO).

## Kernregel

**Eén stap per beurt.** Nooit de hele checklist in één keer dumpen.

Per beurt geef je:
1. **Waar we zijn** — stap X van Y + korte titel
2. **Wat jij nu doet** — max 3 korte instructies (actie in de app)
3. **Eén vraag** — meerkeuze via `AskQuestion`, anders open tekst of screenshot
4. **Ruimte voor extra's** — expliciet uitnodigen tot aanvullingen

## Wanneer starten

- Gebruiker roept `/hilt` aan (met of zonder taaknaam)
- Issue/PRD met open HILT-checklist
- Na `/planning-overzicht` — gebruiker kiest een HILT-rij
- Vóór merge wanneer handcheck vereist is

## Sessie starten

1. **Checklist vinden** — in deze volgorde:
   - Expliciet pad of issue uit gebruikersvraag
   - `.scratch/*/HILT*.md`, `HANDCHECK*.md`
   - `KANBAN_HANDOFF.md` — sectie Haarlem/handcheck
   - Issue-body met HILT acceptance criteria
2. **Kort voorlezen** — doel in één zin + geschat aantal stappen
3. **Voorbereiding** — alleen wat nodig is voor stap 1 (app starten, fixture, env-flag)
4. **Begin stap 1** — met één vraag

Geen checklist gevonden? Vraag welke taak, of bied keuze uit open HILT-items (`/planning-overzicht`).

## Stap-voor-stap protocol

### Structuur per beurt

```markdown
## Stap [X]/[Y] — [korte titel]

**Doe dit:**
- [actie 1]
- [actie 2]

**Vraag:** [één eenvoudige vraag]

*(Optioneel: aanvullingen, opmerkingen of een screenshot zijn welkom.)*
```

### Vraag kiezen

| Situatie | Vraagtype |
|----------|-----------|
| Ja/nee, klopt/niet, zichtbaar/onzichtbaar | `AskQuestion` — 2–4 opties |
| GO/NO-GO, akkoord/afwijking | `AskQuestion` — incl. "Deels / twijfel" |
| Keuze tussen vaste uitkomsten | `AskQuestion` |
| Beschrijving, getal, pad, onverwacht gedrag | Open tekst — vraag expliciet om antwoord **of screenshot** |
| Visuele controle | Eerst meerkeuze ("Ziet het er goed uit?"); bij twijfel: screenshot |

**Meerkeuze-opties** — kort, actiegericht, één duidelijke aanbeveling waar logisch:
- ✅ Klopt / werkt zoals verwacht
- ❌ Klopt niet — ik licht toe
- 🤔 Twijfel — ik stuur screenshot of toelichting
- ⏭️ Stap overslaan (met reden)

Voeg altijd **"Anders / toelichting"** toe als escape hatch.

### Na elk antwoord

1. **Registreer** — kort in sessiegeheugen (stap, antwoord, eventuele notities)
2. **Reageer** — bevestig; bij afwijking: geen paniek, noteer bevinding, bespreek of blocking
3. **Volgende stap** — pas na bevestiging; bij blocking defect: stop GO-pad, bied bug-registratie
4. **Aanvullingen** — als gebruiker extra geeft: verwerk vóór volgende stap

### Blocking vs non-blocking

| Signaal | Actie |
|---------|--------|
| Kern-AC faalt | Geen GO; documenteer; bied issue/fix |
| Cosmetisch / minor | Noteer; vraag of GO met known gap |
| Onzeker | Vraag screenshot of herhaal substap |

## Sessie afsluiten

Laatste stap: **GO/NO-GO** via `AskQuestion`:

- **GO** — alles getest, akkoord
- **GO met kanttekening** — akkoord met genoteerde gaps
- **NO-GO** — blocking; reden volgt
- **Later verder** — sessie pauzeren

Na GO (met toestemming gebruiker):
- Update checklist (`[x]`, notitietabel, datum) in bronbestand
- Kort rapport: wat getest, bevindingen, uitkomst
- Geen commit tenzij gevraagd

## rcm-desktop defaults

- App: `python -m rcm_desktop.main` (venv)
- Fixture Haarlem: `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`
- Meekoppel v2: `RCM_MEEKOPPEL_WORKFLOW_V2=1`
- Legacy validate: `--legacy-validate` / `RCM_LEGACY_VALIDATE=1`
- Bekende checklists: zie [reference.md](reference.md)

## Kwaliteitsregels

- **Eén vraag per beurt** — nooit twee vragen tegelijk
- **Kort** — instructies scanbaar; geen lange proza
- **Geen aannames** — niet invullen wat de gebruiker zag
- **Geen AFK-werk** tijdens HILT — geen code tenzij expliciet blocking + gebruiker vraagt fix
- **Screenshots** — bij visuele twijfel actief vragen; niet zelf raden

## Voorbeeld (ingekort)

**Beurt 1:**
> ## Stap 1/8 — App starten
> **Doe dit:** Start de resultatenwerkruimte.
> **Vraag:** Is het venster zonder foutmelding geopend?
> *(Aanvullingen welkom.)*

→ `AskQuestion`: Ja / Nee met foutmelding / Anders

**Beurt 2** (alleen na antwoord):
> ## Stap 2/8 — Vergelijkingsmenu
> …

## Extra bronnen

- Checklist-locaties en vraag-sjablonen: [reference.md](reference.md)
