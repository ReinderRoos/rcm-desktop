# PRD — Slice 87: Input entiteiten-grid — PBS-scope, zoekbalk en performance

**Status:** ready-for-agent
**Voorganger:** slice 83 (generiek entiteiten-grid), slice 81 (tabel-filterrij), slice 86 (PBS-navigatie)
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van de `/grill-with-docs`-sessies (2026-06-11), inclusief ADR-0014
> en technische uitwerking. Vervangt de per-kolom filterrij op Input door
> PBS-scope + globale zoekbalk; bundelt performance-fixes voor laadtijd en
> kolomkeuze.

---

## Problem Statement

De vijf Input-tabellen (entiteiten-grid, slice 83) laden en reageren traag.
De volledige **tabel-filterrij** (slice 81) op Input creëert per kolom Qt-
widgets en triggert herhaalde `rows()`-berekeningen bij elke filter- en
cel-pass. Voor grote modellen is **PBS-scope** (subtree-selectie in de
werkruimte-boom) de natuurlijke navigatie-as — analisten focussen al op een
onderdeel via dezelfde boom als Output. Per-kolom filters op Input leveren
weinig extra waarde t.o.v. die scope plus één zoekveld. Kolomkeuze triggert
bovendien een volledige `attach()`-rebuild, wat interactie vertraagt.

## Solution

Vanuit de gebruiker gezien:

- Input-tabellen hebben **geen per-kolom filterrij** meer; Output (FM-
  resultaten) behoudt de volledige filterrij ongewijzigd.
- Op PBS-gebonden Input-views (**Faalwijzen**, **REV-taken**, **Correctief
  onderhoud**) volgt de tabel automatisch de actieve **PBS-scope** uit de
  werkruimte-boom — dezelfde presentatiesemantiek als Output, geen deelrun.
- Elke Input-view heeft één **globale zoekbalk** (deelstring, hoofdletter-
  ongevoelig) die combineert met PBS-scope (EN).
- **Effecten** en **Taakgroepen** tonen altijd het volledige project; bij
  actieve scope verschijnt een subtiele statusregel dat PBS-scope daar niet
  geldt.
- Naast de zoekbalk toont een **rijtelling** hoeveel rijen zichtbaar zijn
  t.o.v. het totaal.
- Input-vensters laden merkbaar sneller; kolomkeuze wisselt zichtbaarheid
  zonder het hele grid opnieuw op te bouwen.
- Bewerken, dirty-markering en opslaan werken ongewijzigd; scope en zoek
  zijn puur presentatie.

---

## Zoom-out: modulekaart

```
   workspace_state.scope_id  (bestaand)
        │
        ▼
   Input-scope-policy (Qt-vrij, NIEUW)  ── view → pbs_bound | project_wide
        │  row → pbs_id (direct of via fm_id)
        │  hergebruikt collect_pbs_subtree_ids
        ▼
   Input-zoektekst-builder (Qt-vrij, NIEUW)  ── key_field + zichtbare kolommen
        │
        ▼
   Input-filter-proxy (views, NIEUW)  ── scope ∧ zoek (patroon FaalwijzenFilterProxy)
        │  bovenop
        ▼
   EntityTableModel → EntityEditService (rows()-cache NIEUW)
        │
        ▼
   Entiteiten-grid-panel (views)  ── zoekbalk + statusregel + rijtelling
        │  kolomkeuze via setColumnHidden (geen full attach)
        ▼
   Resultatenwerkruimte-venster  ── scope-wissel → panel.set_scope()
```

Betrokken seams (domeintaal → module):

- **PBS-scope op Input** (ADR-0014, CONTEXT.md) — presentatiefilter op
  proxy-niveau; `edit_current` blijft projectbreed.
- **collect_pbs_subtree_ids** (bestaand, `result_filter_service`) —
  subtree-bepaling hergebruiken; geen nieuwe PBS-logica.
- **Input-scope-policy (NIEUW, Qt-vrij)** — per view-id: PBS-gebonden of
  projectbreed; per rij: welke `pbs_id` geldt voor scope-check.
- **Input-zoektekst (NIEUW, Qt-vrij)** — haystack per rij voor globale
  zoekbalk.
- **Input-filter-proxy (NIEUW)** — generieke `QSortFilterProxyModel` met
  `scope_subtree` ∧ `search_text`.
- **EntityEditService** — cache op `rows()`; invalideren bij mutaties.
- **Entiteiten-grid-panel** — vervangt filterrij-binding door zoekbalk-UI;
  lichte kolomtoggle.
- **Tabel-filterrij** (slice 81) — blijft alleen op Output; Input-pad
  ontkoppelen.

## Implementation Decisions

### Filterbeleid (ADR-0014)

- **Input ≠ Output:** FM-resultaten houden `TableColumnFilterProxy` +
  `TableFilterRowWidget`; entiteiten-grid niet.
- **Geen domein-comboboxes** op Input (Faalwijzen-batch-grid in
  `ValidateFaalwijzenPanel` blijft ongewijzigd).
- **Globale zoekbalk:** één `QLineEdit` per view in de grid-toolbar.
- **Zoektekst niet persistent** tussen sessies (zelfde beleid als
  Output-filterrij).
- **Zoektekst gewist** bij view-wissel; **behouden** bij PBS-scope-wissel.

### PBS-scope op Input

- Bron: `workspace_state.scope_id`; subtree via `collect_pbs_subtree_ids`.
- **`scope_id=None`:** heel project zichtbaar (geen scope-filter).
- **Onbekende `scope_id`:** lege tabel op PBS-gebonden views (zelfde als
  Output).
- **PBS-gebonden views:**
  - Faalwijzen, Correctief: directe `pbs_id` op de rij.
  - REV-taken: `fm_id` → faalwijze.`pbs_id` in het project.
- **Projectbreed (geen PBS-filter):** Effecten, Taakgroepen — altijd alle
  rijen; bij actieve scope: subtiele statusregel *"PBS-scope niet van
  toepassing — toont alle {entiteit}"*.
- Scope-wissel: alleen proxy bijwerken (`beginFilterChange`/`endFilterChange`);
  geen `attach()` of service-reset.
- Werkruimte-venster roept bij `set_pbs_scope` en bij grid-`attach` de
  huidige scope op het panel aan.

### Globale zoekbalk — zoekbereik

- Substring, hoofdletterongevoelig; combineert als EN met PBS-scope.
- Doorzoekt per rij:
  - **key_field** altijd (ook als kolom verborgen via kolomkeuze).
  - Alle **zichtbare** kolommen: zowel **displaytekst** als **ruwe waarde**
    (bv. `random` én gelokaliseerd faaltype-label; `fm_id` én omschrijving).
  - Afgeleide kolommen (PM-schedule) meenemen wanneer zichtbaar.
- Zoek vindt geen rijen buiten actieve PBS-scope (scope heeft voorrang).

### Dirty-gedrag onder scope (grill-besluit)

- Scope is **puur presentatie**; wijzigingen buiten zichtbare scope blijven
  dirty en worden normaal opgeslagen.
- **Geen** extra waarschuwing, bevestiging of indicator voor dirty rijen
  buiten scope (ADR-consistent, optie A).

### Performance — `rows()`-cache

- `EntityEditService.rows()` cached gesorteerde `EntityRowView`-lijst.
- Invalideren bij: `apply_change`, `apply_bulk_change`, `discard_changes`,
  `reset`/`init`, `attach_editing_session`, `clear`.
- Geen `CACHE_INPUTS_VERSION`-bump; geen `rcm_core`-wijziging.

### Performance — kolomkeuze

- Tabelmodel bevat **alle** schema-kolommen (preset + optional).
- Verborgen kolommen via `QTableView.setColumnHidden()`; persistentie via
  bestaande `QSettings`-flow.
- `attach()` alleen bij view-wissel of service/project-reset — **niet** bij
  kolomtoggle.
- Faalwijzen-delegates eenmalig bij `attach` op vaste kolomindexen.

### Op te ruimen

- Input-pad ontkoppelen van `entity_grid_filter_binding` en
  `entity_filter_policy` (verwijderen indien geen andere afnemer).
- Bestaande slice-83-test `set_text_filter` / per-kolom filter vervangen door
  zoekbalk- en scope-tests.

### Documentatie

- ADR-0014 en CONTEXT.md zijn reeds bijgewerkt; geen extra ADR in deze slice.
- Labels/placeholders via `messages`.

### Grenzen

- **Lazy attach** (grid alleen binden wanneer Input zichtbaar): **niet** in
  deze slice — aparte follow-up.
- **Geen** wijziging aan Validate-venster of Faalwijzen-batch-grid.

## User Stories

1. Als RCM-analist wil ik dat Input-tabellen sneller laden, zodat ik zonder
   wachttijd kan beginnen met beoordelen en bewerken.
2. Als analist wil ik op Faalwijzen, REV-taken en Correctief automatisch
   alleen rijen in de actieve PBS-scope zien, zodat ik hetzelfde bouwdeel
   volg als in Output zonder apart te filteren.
3. Als analist wil ik bij Effecten en Taakgroepen altijd het volledige
   project zien, zodat gedeelde entiteiten niet ten onrechte worden
   weggefilterd.
4. Als analist wil ik bij Effecten/Taakgroepen een duidelijke melding wanneer
   PBS-scope elders actief is maar hier niet geldt, zodat ik niet denk dat
   rijen ontbreken door een bug.
5. Als analist wil ik één zoekveld per Input-tabel, zodat ik snel op id of
   omschrijving kan zoeken zonder per kolom te typen.
6. Als analist wil ik hoofdletterongevoelig kunnen zoeken, zodat ik niet op
   exacte schrijfwijze hoef te letten.
7. Als analist wil ik zoeken en PBS-scope gecombineerd (EN), zodat ik binnen
   een bouwdeel verder kan verfijnen.
8. Als analist wil ik dat zoeken ook de rij-id vindt wanneer die kolom
   verborgen is, zodat kolomkeuze de zoekfunctie niet breekt.
9. Als analist wil ik dat zoeken zowel op weergavetekst als op ruwe waarden
   matcht, zodat ik bv. op faaltype-code én op het Nederlandse label kan
   zoeken.
10. Als analist wil ik een rijtelling (gefilterd van totaal), zodat ik zie
    hoeveel rijen scope en zoek hebben achtergelaten.
11. Als analist wil ik dat PBS-scope-wissel mijn zoektekst behoudt, zodat ik
    dezelfde zoekterm in een ander bouwdeel kan hergebruiken.
12. Als analist wil ik dat view-wissel de zoektekst wist, zodat ik niet per
    ongeluk filter van Faalwijzen op REV-taken toepas.
13. Als analist wil ik dat filterwaarden niet tussen sessies bewaard blijven,
    zodat ik na herstart niet met een onzichtbaar actief filter zit.
14. Als analist wil ik kolommen kunnen tonen/verbergen zonder merkbare
    vertraging, zodat kolomkeuze een lichte actie blijft.
15. Als analist wil ik dat mijn kolomkeuze nog steeds per view persistent is,
    zodat mijn werksetup behouden blijft.
16. Als analist wil ik dat celbewerkingen, validatie en foutmarkering
    ongewijzigd werken, zodat ik dezelfde editing-regels houd als vóór deze
    slice.
17. Als analist wil ik dat wijzigingen buiten de actieve scope nog steeds
    worden opgeslagen wanneer ik opsla, zodat de bewerkingsbuffer één
    waarheid blijft.
18. Als analist wil ik dat FM-resultaten hun volledige per-kolom filterrij
    behouden, zodat Output-analyse niet verslechtert.
19. Als analist wil ik dat het Faalwijzen-grid in het Validate-venster
    ongewijzigd blijft, zodat bestaande workflows niet breken.
20. Als analist wil ik bij onbekende of ongeldige PBS-scope een lege tabel
    zien op PBS-gebonden views, zodat het gedrag voorspelbaar is (zoals
    Output).
21. Als analist wil ik dat een run op het volledige project start, ook wanneer
    ik een PBS-scope actief heb op Input, zodat scope geen stille deelrun
    wordt.
22. Als ontwikkelaar wil ik PBS-scope-regels per view declaratief en Qt-vrij
    testbaar, zodat nieuwe Input-views goedkoop aansluiten.
23. Als ontwikkelaar wil ik dat de filter-proxy generiek is (niet Faalwijzen-
    specifiek), zodat alle vijf views dezelfde implementatie delen.

## Testing Decisions

Goede tests toetsen **extern gedrag** aan de hoogst mogelijke seam — niet
widget-internals of private cache-velden.

### Voorgestelde test-seams (hoog → laag)

| Prioriteit | Seam | Wat wordt getest |
|------------|------|------------------|
| 1 | **Input-scope-policy** (Qt-vrij) | Per view-id: `pbs_bound` vs `project_wide`; `row_pbs_id` voor faalwijzen, rev_tasks (via fm), correctief; rij in/uit subtree |
| 2 | **Input-zoektekst-builder** (Qt-vrij) | Haystack bevat key_field, display en ruwe waarden; match op substring |
| 3 | **EntityEditService.rows()** (adapter) | Twee opeenvolgende `rows()` na mutatie: inhoud klopt; cache gedrag via observabele uitkomst (geen private asserts) |
| 4 | **Input-filter-proxy** (pytest-qt, geïsoleerd) | Scope alleen, zoek alleen, EN-combinatie, lege subtree |
| 5 | **Entiteiten-grid-panel** (pytest-qt) | Geen filterrij-widgets; zoekbalk vermindert zichtbare rijen; rijtelling; kolomtoggle zonder row_count-reset van service |
| 6 | **Resultatenwerkruimte-venster** (pytest-qt, dun) | Scope-wissel op Input Faalwijzen vermindert rijen; Effecten toont statusregel bij actieve scope |

**Bevestiging:** deze seams volgen het bestaande patroon (Qt-vrij eerst,
`FaalwijzenFilterProxy`/`result_filter_service` als prior art, venstertests
alleen waar wiring nodig is).

### Regressie en prior art

- `tests/test_editing_schemas_parity.py` blijft groen.
- FM-resultaten filterrij-tests (slice 81) ongewijzigd groen.
- Vervang slice-83 `set_text_filter`-test door zoekbalk-equivalent.
- Prior art: `FaalwijzenFilterProxy`, `collect_pbs_subtree_ids` /
  `filter_run_result`, `test_slice83_entity_grid.py`,
  `test_slice81_*`.

### Wat niet testen

- Exact aantal Qt-widgets of `attach()`-aanroepen (implementatiedetail).
- Performance-benchmarks als harde CI-gate (optioneel handmatig).
- Validate-venster Faalwijzen-grid (out of scope).

## Out of Scope

- **Lazy attach** — grid pas binden wanneer Input-zijde zichtbaar is.
- Wijzigingen aan Validate-venster / `ValidateFaalwijzenPanel`.
- Per-kolom filterrij op Input (herstel vereist ADR-0014-revisie).
- PBS-scope op Effecten/Taakgroepen via indirecte PM-referenties.
- Domein-comboboxes op Input (faaltype, NMF, …).
- `rcm_core`- of schema-wijzigingen; geen `CACHE_INPUTS_VERSION`-bump.
- Waarschuwingen of indicators voor dirty wijzigingen buiten actieve scope.
- Persistentie van zoektekst tussen sessies.

## Further Notes

- Slice 83 PRD vermeldde filterrij op Input; deze slice **supersede** dat
  onderdeel conform ADR-0014. Output blijft slice-81-conform.
- De Correctief-projectie deelt nog steeds de editing-sessie met Faalwijzen;
  scope op Correctief gebruikt `pbs_id`, op REV-taken `fm_id` → faalwijze.
- Bij implementatie: let op regelbudget `results_workspace_window.py` — scope-
  doorgeeflijn in een dunne binding/helper houden.
- Issue-splitting: tracer bullet = scope-policy + zoektekst + proxy + Faalwijzen-
  view; vervolgissues voor overige views, `rows()`-cache, kolomkeuze-fix.
