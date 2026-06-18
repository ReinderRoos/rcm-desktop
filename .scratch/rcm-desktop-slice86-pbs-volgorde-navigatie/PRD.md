# PRD — Slice 86: PBS-volgorde + navigatie-/reorder-sneltoetsen (+ ADR)

**Status:** ready-for-agent
**Voorganger:** slice 79 (view-registry/sneltoetsen), slice 76 (menubalk)
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van de `/grill-with-docs`-sessie (2026-06-11), besluiten 13 en 14.
> Inclusief ADR **"Presentatievelden buiten de cache-vingerafdruk"**.

---

## Problem Statement

De volgorde van PBS-items in de boom is vandaag impliciet (invoer-/
importvolgorde); de analist kan een bouwdeel niet boven een ander zetten —
bijvoorbeeld *Brug* boven *Schutsluis* — terwijl die presentatievolgorde in
rapportages en reviews betekenis heeft. Daarnaast is de PBS-boom alleen met
de muis te bedienen: er zijn geen sneltoetsen om een niveau op of neer te
gaan, de diepte in of uit te navigeren, of een item binnen zijn niveau te
verplaatsen. Een naïeve oplossing (volgorde opnemen in het model en dus in de
cache-vingerafdruk) zou elke herordening bestraffen met een volledige
her-run, terwijl er rekenkundig niets verandert.

## Solution

Vanuit de gebruiker gezien:

- PBS-items kunnen **binnen hun niveau** (tussen broers/zussen) van volgorde
  wisselen; de boom, tabellen en rapportages volgen die volgorde.
- Sneltoetsen:
  - `Alt+↑` / `Alt+↓` — selectie naar vorige/volgende item op het niveau;
  - `Alt+←` / `Alt+→` — naar parent / eerste kind (de diepte in/uit);
  - `Ctrl+Alt+↑` / `Ctrl+Alt+↓` — geselecteerd item één positie omhoog/
    omlaag verplaatsen binnen zijn niveau.
- Herordenen markeert het project dirty en wordt opgeslagen in het
  projectbestand, maar **triggert géén her-run**: resultaten blijven geldig.

---

## Zoom-out: modulekaart

```
   rcm_core/models.py  ── PBSItem + volgorde-veld (NIEUW)
        │  to_dict()/from_dict(): wel persistentie
        │  globale digest + FM-invoerhash: UITGESLOTEN
        ▼
   Adapter: PBS-boommodel  ── sortering op (volgorde, bestaande fallback)
        │  reorder-operatie (swap met buur) via editing-flow
        ▼
   PBS-zijbalk (view)  ── sneltoetsen → navigatie/reorder-handlers
   Menubalk-spec  ── items + sneltoetsen geregistreerd (uniciteitscheck)
```

Betrokken seams (domeintaal → module):

- **Domain model** (`rcm_core/models.py`, `PBSItem`) — nieuw veld
  `volgorde` (int), default zo dat bestaande projecten hun huidige volgorde
  behouden; mee in `to_dict()`/`from_dict()` (`.rcm.json`).
- **Globale digest / FM-invoerhash** (`rcm_core`) — `volgorde` expliciet
  **uitgesloten** van beide vingerafdrukken: herordenen ≠ rekeninput.
- **Editing schema registry** (`rcm_core/editing/schemas.py`) — `volgorde`
  als veld op de pbs-entiteit; **parity-tests** bijwerken (AGENTS.md: anders
  is het drift).
- **PBS-boommodel (adapter)** — sorteert broers/zussen op `volgorde`;
  reorder = volgorde-swap met de buur, via de normale editing/dirty-flow.
- **Menubalk-spec** (slice 76) — navigatie- en reorder-acties als menu-items
  met sneltoetsen, zodat de uniciteitsvalidatie ze dekt.

## Implementation Decisions

- **Alleen sibling-reordering** (besluit 13): verplaatsen wijzigt nooit de
  parent — geen re-parenting, geen niveau-wissel. "Brug boven Schutsluis"
  is een volgorde-swap binnen hetzelfde niveau.
- **Expliciet `volgorde`-veld op `PBSItem`** (besluit 14), gepersisteerd in
  `.rcm.json`. Migratie: ontbrekend veld → volgorde = huidige positie
  (import-/leesvolgorde), zodat bestaande projecten identiek renderen.
- **Uitgesloten van digest én FM-invoerhash** (besluit 14): herordenen
  markeert dirty (opslaan nodig) maar invalideert geen cache en triggert
  geen her-run. Dit is de kern van de bijbehorende **ADR
  "Presentatievelden buiten de cache-vingerafdruk"**: wel in `to_dict()`,
  niet in de vingerafdrukken; inclusief het criterium wanneer een veld
  "presentatie" is.
- **Sneltoetsmap** (besluit 13): `Alt+↑/↓` (navigatie binnen niveau),
  `Alt+←/→` (diepte uit/in), `Ctrl+Alt+↑/↓` (reorder). Registratie via de
  menubalk-spec; conflictcontrole met bestaande sneltoetsen (o.a. slice 76/79)
  in de spec-validator.
- **Reorder via de editing-flow**: de swap loopt als normale modelbewerking
  (dirty, save, undo voor zover de flow dat kent) — geen apart
  persistentiepad.
- **Geen JSON-vormwijziging in rekeninput** → geen
  `CACHE_INPUTS_VERSION`-bump voor de volgorde zelf; wél parity-tests
  bijwerken omdat `models.py` en `schemas.py` wijzigen.
- **CONTEXT.md**: term *PBS-volgorde* toevoegen.

## User Stories

1. Als RCM-analist wil ik een PBS-item binnen zijn niveau omhoog/omlaag
   verplaatsen, zodat de boom mijn gewenste presentatievolgorde toont.
2. Als analist wil ik bijvoorbeeld *Brug* boven *Schutsluis* zetten, zodat
   rapportage en review mijn objectvolgorde volgen.
3. Als analist wil ik `Ctrl+Alt+↑/↓` voor verplaatsen, zodat herordenen
   zonder muis kan.
4. Als analist wil ik `Alt+↑/↓` om binnen een niveau te navigeren, zodat ik
   snel langs broers/zussen loop.
5. Als analist wil ik `Alt+←/→` om naar parent of eerste kind te springen,
   zodat ik de diepte in en uit kan.
6. Als analist wil ik dat verplaatsen nooit de parent wijzigt, zodat ik niet
   per ongeluk de structuur verbouw.
7. Als analist wil ik dat de nieuwe volgorde wordt opgeslagen in het
   projectbestand, zodat die na heropenen intact is.
8. Als analist wil ik dat herordenen géén her-run veroorzaakt, zodat ik
   vrijelijk kan ordenen zonder rekentijd te verliezen.
9. Als analist wil ik dat herordenen het project wel dirty markeert, zodat ik
   weet dat er iets op te slaan valt.
10. Als analist wil ik dat alle weergaves die PBS-volgorde gebruiken (boom,
    tabellen, rapportage) dezelfde volgorde tonen, zodat er één waarheid is.
11. Als analist wil ik dat bestaande projecten zonder volgorde-veld er exact
    zo uitzien als voorheen, zodat de migratie onzichtbaar is.
12. Als beheerder van de architectuur wil ik een ADR over presentatievelden
    buiten de cache-vingerafdruk, zodat dit patroon herhaalbaar en bewaakt is.

## Testing Decisions

Goede tests toetsen extern gedrag: persistentie, vingerafdruk-stabiliteit en
boomvolgorde — geen widget-internals.

- **Primaire seam (Qt-vrij, `rcm_core`):**
  1. Round-trip: `volgorde` overleeft `to_dict()`/`from_dict()`.
  2. **Vingerafdruk-stabiliteit**: alleen `volgorde` wijzigen → globale
     digest en FM-invoerhash identiek; een rekenveld wijzigen → wel anders
     (controle dat de uitsluiting niet te breed is).
  3. Migratie: project zonder `volgorde` → leesvolgorde behouden.
- **Parity:** `tests/test_editing_schemas_parity.py` bijgewerkt en groen
  (modelveld + schemaveld in sync).
- **Adapter (boommodel):** broers/zussen gesorteerd op volgorde; swap-operatie
  verwisselt precies twee buren en markeert dirty.
- **Menubalk-spec golden:** nieuwe acties + sneltoetsen aanwezig en uniek.
- **pytest-qt (venster):** sneltoetsen navigeren/verplaatsen de selectie;
  reorder is zichtbaar in de boom; geen run wordt gestart na reorder.
- **Prior art:** digest-/incremental-run-tests (seam: patch op
  `rcm_core.incremental_run as ir`), PBS-zijbalk-tests, slice 76-spec-tests.

## Out of Scope

- Re-parenting of niveauwijziging via verplaatsen.
- Drag-and-drop-reordering met de muis (kan later; sneltoetsen eerst).
- Volgorde-doorwerking in de motor of rekenresultaten (per definitie geen).
- Hernummering/normalisatie-UI voor volgordewaarden.

## Further Notes

- De ADR is onderdeel van deze slice; hij dekt ook toekomstige
  presentatievelden (criterium + testpatroon "vingerafdruk-stabiliteit").
- Let op de bestaande seam-afspraak: incrementeel/cache-gedrag testen via
  patch op `rcm_core.incremental_run as ir`.
- Sneltoets-conflictrisico: `Alt+pijlen` kan met Qt-default
  focusnavigatie botsen; vang dit af op de PBS-boom (alleen actief bij
  boomfocus) en documenteer dit in de spec.
