# PRD — Slice 81: Tabel-filterrij (herbruikbare filter-proxy)

**Status:** ready-for-agent
**Voorganger:** slice 80 (FM-resultaten-tabel)
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van de `/grill-with-docs`-sessie (2026-06-11), besluit 7.
> Eerste afnemer: FM-resultaten; tweede afnemer: het entiteiten-grid (slice 83).

---

## Problem Statement

Geen enkele werkruimte-tabel is vandaag per kolom filterbaar. Wie in
FM-resultaten alleen de faalwijzen van één bouwdeel wil zien, of alleen
NMF-faalwijzen, of alleen rijen met kosten boven een drempel, moet visueel
scannen of exporteren. Bestaande filters (PBS-boomfilter, NB-effectfilter)
werken op andere assen en helpen hier niet. Tegelijk komen er met de
Input-tabellen (slice 83) nog vijf tabellen aan die exact dezelfde behoefte
hebben — vijf ad-hoc filterimplementaties zou drift garanderen.

## Solution

Vanuit de gebruiker gezien:

- Onder de kolomkoppen van FM-resultaten verschijnt een **filterrij**: per
  kolom een invoerveld.
- **Tekstkolommen** (Bouwdeel, Faalwijze, FM-id, …) filteren op
  **deelstring**, hoofdletterongevoelig.
- **Booleankolommen** (NMF) filteren via ja/nee/alles.
- **Numerieke kolommen** (Faalmomenten, Downtime, Kosten, RF) accepteren
  **expressies**: `>100`, `<=0.5`, `10..50`, of een kaal getal (exact).
- Filters combineren als EN over kolommen; een wisknop maakt alle filters
  leeg. De rijtelling toont gefilterd/totaal.

---

## Zoom-out: modulekaart

```
   Filterrij-widget (view, dunne laag)
            │ kolom → filtertekst
            ▼
   Filter-spec + parser (Qt-vrij, NIEUW)   ── deelstring | bool | expressie
            │ per kolom een predikaat
            ▼
   Filter-proxy (QSortFilterProxyModel, generiek)
            │ gestapeld op
            ▼
   FM-resultaten-sort-proxy → tabelmodel          (later: entiteiten-grid)
```

Betrokken seams (domeintaal → module):

- **Filter-spec + parser (NIEUW, Qt-vrij)** — per kolomtype
  (tekst/bool/numeriek) zet een pure functie de invoertekst om in een
  predikaat; foutieve expressies leveren een "alles tonen"-predikaat +
  foutmarkering, geen crash.
- **Generieke filter-proxy (NIEUW)** — één `QSortFilterProxyModel`-subklasse
  in de sfeer van `workspace_table_policy`, geconfigureerd met kolomtypen;
  kent geen FM-specifieke logica.
- **FM-resultaten-view** — filterrij-widget onder de header, bind-only.

## Implementation Decisions

- **Eén herbruikbare seam** (besluit 7): de filter-proxy + parser zijn
  generiek en tabel-agnostisch; FM-resultaten is de eerste afnemer, het
  entiteiten-grid (slice 83) de tweede. Geen FM-kennis in de proxy.
- **Filtersemantiek per kolomtype**: deelstring (case-insensitive,
  genormaliseerd) voor tekst; drie-standenfilter voor bool; expressiegrammatica
  voor numeriek: `>`, `>=`, `<`, `<=`, `=`, bereik `a..b`, kaal getal = exact
  (met decimale komma én punt geaccepteerd).
- **Stapeling**: filter-proxy bovenop de bestaande sort-proxy (of andersom,
  als één keten) — sorteren en filteren blijven onafhankelijk werken.
- **Filtering is presentatie**: KPI's en plots blijven op de ongefilterde
  dataset werken; alleen de tabelrijen worden beperkt. De rijtelling
  (gefilterd/totaal) maakt dit zichtbaar.
- **Geen persistentie van filterwaarden** tussen sessies (bewuste keuze:
  een onzichtbaar actief filter na herstart is verwarrender dan opnieuw
  typen).
- Labels/placeholder-teksten via `messages`.
- **CONTEXT.md**: term *Tabel-filterrij* toevoegen.

## User Stories

1. Als RCM-analist wil ik onder elke kolomkop van FM-resultaten een
   filterveld, zodat ik de tabel verfijn zonder te exporteren.
2. Als analist wil ik Bouwdeel en Faalwijze op **deelstring** filteren, zodat
   "cilin" alle cilinder-varianten vindt.
3. Als analist wil ik hoofdletterongevoelig filteren, zodat ik niet op
   exacte schrijfwijze hoef te letten.
4. Als analist wil ik de NMF-kolom op ja/nee filteren, zodat ik alleen
   niet-merkbare faalwijzen zie.
5. Als analist wil ik numerieke kolommen met `>`, `<`, `>=`, `<=` en
   bereiken filteren, zodat ik bijvoorbeeld alleen kosten boven €10.000 zie.
6. Als analist wil ik filters over meerdere kolommen combineren (EN), zodat
   ik gericht kan inzoomen.
7. Als analist wil ik één wisknop voor alle filters, zodat ik snel terug ben
   bij het volledige beeld.
8. Als analist wil ik zien hoeveel rijen van het totaal zichtbaar zijn, zodat
   een actief filter nooit onopgemerkt blijft.
9. Als analist wil ik dat een ongeldige expressie de rij niet leegt maar als
   fout gemarkeerd wordt, zodat een typo geen paniek veroorzaakt.
10. Als analist wil ik dat sorteren en filteren samen werken, zodat ik
    gefilterde rijen ook gesorteerd zie.
11. Als ontwikkelaar wil ik dezelfde filterrij later op de Input-tabellen
    zetten met alleen configuratie (kolomtypen), zonder nieuwe filterlogica.

## Testing Decisions

Goede tests toetsen extern gedrag aan de Qt-vrije parser en de generieke
proxy — niet aan de widget.

- **Primaire seam (Qt-vrij): de expressie-parser.**
  1. Tabelgedreven tests: invoertekst × kolomtype → predikaatgedrag
     (deelstring, bool, `>100`, `10..50`, komma-decimalen, lege invoer).
  2. Ongeldige expressie → alles-tonen + foutvlag.
- **Filter-proxy (pytest-qt, headless model):** EN-combinatie over kolommen;
  stapeling met sort-proxy; rijtelling.
- **pytest-qt (venster):** filterrij zichtbaar in FM-resultaten; typen in
  Bouwdeel-filter beperkt rijen; wisknop herstelt; KPI's veranderen niet mee.
- **Prior art:** `_PBSSidebarFilterProxy` (bestaande proxy-aanpak),
  `tests/test_workspace_table_policy*.py` (policy-seam-tests).

## Out of Scope

- Filterrij op de Input-tabellen (slice 83 hergebruikt deze seam).
- OF-combinaties, regex-invoer of een query-taal.
- Persistentie van filterwaarden tussen sessies.
- Doorwerking van tabelfilters in KPI's, plots of export.

## Further Notes

- Parser en proxy bewust scheiden: de parser is puur en snel te testen; de
  proxy is dun Qt-bindwerk.
- De NMF-kolom uit slice 80 is de eerste boolean-afnemer; ontwerp het
  drie-standenfilter (alles/ja/nee) daarop.
