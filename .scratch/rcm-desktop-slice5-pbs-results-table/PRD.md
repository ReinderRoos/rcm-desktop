# PRD — RCM2 desktop slice 5 (PBS-resultatentabel onder `run --full`)

**Status:** ready-for-agent
**Versie:** 1.0
**Triage-labels:** zie `../../AGENTS.md`

## Bron / context

- `../../README.md`
- `../../AGENTS.md`
- `../../CONTEXT.md`
- `../../../rcm/.scratch/rcm2-restart-reference/RCM2_REFERENTIE.md`
- Voorgaande slices:
  - `../rcm-desktop-slice1-validate/`
  - `../rcm-desktop-slice2-preview/PRD.md`
  - `../rcm-desktop-slice3-run/PRD.md`
  - `../rcm-desktop-slice4-results-table/PRD.md`
- Design-interview (vastgelegde beslissingen): zie sectie *Implementation
  decisions*.

## Problem statement

Na slice 1 + 2 + 3 + 4 ziet de analist na een geslaagde `run --full` drie
KPI-getallen plus een sorteerbare faalwijzen-tabel — hij kan dus
prioriteren *welke faalwijze* het zwaarst telt. Wat ontbreekt is de
**tweede rangorde-dimensie**: *welk bouwdeel* (PBSItem) draagt het meest
bij aan kosten, faalmomenten of niet-beschikbaarheid? Voor een gerichte
onderhoudsbeslissing wil de analist niet alleen "deze faalwijze" maar
ook "dit bouwdeel inclusief alles eronder" zien.

`rcm_core.incremental_run.IncrementalRunResult` levert al
`pbs_results: dict[str, PBSResult]` en de PBS-hiërarchie zit in
`PBSItem.parent_pbs_id`. De data is dus aanwezig; alleen de
UI-laag exposed hem nog niet, en de adapter heeft nog geen pure
view-mapping plus geaggregeerde rollups langs de boom.

## Solution

Voeg een verticale slice toe die direct ná de FM-tabel een sorteerbare
PBS-tabel toont, met per rij zowel de eigen bijdrage als de geaggregeerde
som over alle descendants:

1. **Run-resultaat verrijken**: het bestaande `RunResult` (slice 3 + 4)
   krijgt additief het veld `pbs_rows: list[PBSResultRow]` (default `[]`).
2. **Pure row-builder met DFS-aggregatie**: in de bestaande module
   `rcm_desktop.adapter.result_view_service` komt een `PBSResultRow`-
   dataclass plus `build_rows`-zustertje
   `build_pbs_rows(project, pbs_results) -> list[PBSResultRow]`. Pure
   functie, geen Qt, geen state, deterministische volgorde.
3. **Eigen Qt-tabelmodel**: `PBSResultsTableModel(QAbstractTableModel)`
   in de adapterlaag. Sortering via `QSortFilterProxyModel` met
   `setSortRole(Qt.UserRole + 1)` — zelfde mechanica als slice 4.
4. **Tabel-paneel onder de FM-tabel** in `validate_window`, zichtbaar bij
   `last_run.status == "done"` én niet-lege `pbs_rows`. **Default-render
   = DFS-volgorde, geen actieve sort** (zodat parent-child meteen
   leesbaar is); user-klik op een header schakelt over op flat sort.
5. **Indent-prefix in Bouwdeel-kolom** en expliciete `level`-kolom maken
   parent-child structureel zichtbaar — ook na user-sort.
6. **Forward-compat**: `list[PBSResultRow]` is modelagnostisch, zodat een
   latere slice `PBSResultsTreeModel(QAbstractItemModel)` met
   expand/collapse op exact dezelfde input kan draaien zonder
   contractwijziging. Latere PM/CM-uitsplitsing op kosten *én* downtime
   wordt additieve velduitbreiding op `PBSResultRow`.
7. **Reset-discipline en empty-state** consistent met slice 4 (paneel
   hidden + model leeg bij pad-wijziging, nieuwe validate, nieuwe run,
   run-error, `None`).
8. **Vocabulaire**: alle nieuwe NL-strings hanteren **"faalmomenten"** en
   **"niet-beschikbaarheid"**.

## User stories

1. Als analist wil ik na een geslaagde `run --full` direct een tabel met
   alle PBS-resultaten zien, zodat ik *bouwdeelniveau* kan prioriteren
   bovenop de faalwijzen-rangorde.
2. Als analist wil ik per PBS-rij zowel de eigen bijdrage als de
   geaggregeerde som over alle onderliggende PBS-items zien, zodat ik
   meteen weet of de totaal-impact bij dit bouwdeel of bij zijn
   sub-componenten zit.
3. Als analist wil ik bij eerste render een hiërarchisch leesbare
   volgorde (root → kinderen → kleinkinderen) zien, zodat ik direct
   begrijp waar items in de boom hangen.
4. Als analist wil ik bij elke nieuwe `done`-run dezelfde DFS-volgorde
   krijgen, zodat eerdere user-sort-keuzes nooit een vorig resultaat
   visueel naar voren halen.
5. Als analist wil ik op kosten, faalmomenten, downtime en
   niet-beschikbaarheid kunnen sorteren, zodat ik per dimensie een
   andere top kan kiezen.
6. Als analist wil ik in de Bouwdeel-kolom visueel kunnen aflezen op
   welk niveau een rij hangt (indent-prefix), zodat ik na een
   user-sort op kosten nog steeds weet wat parent en wat child is.
7. Als analist wil ik een expliciete Niveau-kolom, zodat ik bij elke
   sortering direct het diepteniveau kan aflezen — ook als de
   indent-affordance wegvalt.
8. Als analist wil ik dat numerieke waarden in de tabel NL-leesbaar
   zijn (duizendpunt, decimaalkomma, euro-prefix, %-suffix), zodat de
   weergave consistent is met de rest van de UI.
9. Als analist wil ik dat de tabel verdwijnt zodra ik het pad wijzig,
   opnieuw valideer of opnieuw run, zodat ik nooit naar verouderde
   PBS-resultaten kijk.
10. Als analist wil ik dat bij een mislukte run (`error`) de PBS-tabel
    niet blijft hangen, zodat foutpaden duidelijk gescheiden blijven van
    geldige uitkomsten.
11. Als analist wil ik dat een run met 0 PBS-resultaten de tabel
    verbergt in plaats van een lege weergave, zodat de UI niet visueel
    ruisig wordt.
12. Als analist wil ik de PBS-tabel zien onder de FM-tabel in dezelfde
    lineaire flow, zodat ik niet tussen vensters hoef te wisselen.
13. Als analist wil ik dat de FM-tabel uit slice 4 onveranderd blijft
    werken naast de nieuwe PBS-tabel, zodat de twee tabellen complementair
    zijn en geen feature regressie veroorzaken.
14. Als analist wil ik dat de tabel-bouw op de werkthread gebeurt zoals
    de FM-tabel-bouw, zodat de UI niet bevriest bij realistische
    projectomvang.
15. Als ontwikkelaar wil ik een pure `build_pbs_rows(project,
    pbs_results)`-functie zonder Qt of state, zodat ik DFS, aggregatie,
    `unavailability_pct_total`-recompute en defensieve cycle/missing-
    parent-handling los kan unit-testen.
16. Als ontwikkelaar wil ik dat `PBSResultRow` zowel `*_self` als
    `*_total` bevat plus `parent_pbs_id`, `level` en `sort_path`, zodat
    een latere treeview-slice geen contractwijziging vereist.
17. Als ontwikkelaar wil ik een eigen `QAbstractTableModel`-subclass in
    de adapter, zodat tabel-rendering en sortering testbaar zijn buiten
    een window.
18. Als ontwikkelaar wil ik dat sortering werkt op raw numerieke waarden
    via `Qt.UserRole + 1`, zodat strings als `"€ 1.200,00"` of
    `"  Bouwdeel"` (met indent) niet als text-volgorde worden
    gesorteerd.
19. Als ontwikkelaar wil ik dat `build_pbs_rows` deterministisch is op
    de child-volgorde binnen één parent (alfabetisch op `pbs_id`), zodat
    tests stabiel blijven los van dict-iteratie-volgorde.
20. Als ontwikkelaar wil ik dat `unavailability_pct_total` deterministisch
    wordt herberekend uit `lifecycle_years × 8760`, zodat de adapter geen
    extra IO of kern-aanroep nodig heeft en parity met
    `pbs_results[pbs_id].unavailability_pct` op single-leaf-PBS getest is.
21. Als ontwikkelaar wil ik dat het rij-contract additief uitbreidbaar
    is voor latere PM/CM-uitsplitsing op kosten *én* downtime, zodat
    een toekomstige slice geen breaking change introduceert.
22. Als reviewer wil ik dat de adapter/views-decoupling uit `AGENTS.md`
    gerespecteerd blijft (geen directe `rcm_core`-imports in views,
    geen Qt-imports in `rcm_core`), zodat de architectuurregels niet
    eroderen.
23. Als reviewer wil ik dat de Qt-tests netjes skippen wanneer `PySide6`
    niet beschikbaar is, zodat de testsuite ook in headless/CI-omgevingen
    consistent draait.

## Implementation decisions

- **Run-contract verrijken (deltachange, additief)**.
  - `rcm_desktop.adapter.run_service.RunResult` krijgt een nieuw veld
    `pbs_rows: list[PBSResultRow]` (default `field(default_factory=list)`).
  - Foutpaden (`RUN_PRECONDITION_NOT_MET`, `RUN_INTERNAL_ERROR`) leveren
    `pbs_rows == []`.
  - `run_service.run` doet de tabel-bouw door in dezelfde aanroep als
    `build_rows(...)` ook `build_pbs_rows(...)` aan te roepen op de
    werkthread. Geen extra service-aanroep, geen extra disk-IO.
  - Bestaande `metrics`/`rows`/`status`/`summary`-velden blijven
    inhoudelijk en testmatig gelijk; alleen het contract groeit additief.

- **Pure adapter-uitbreiding `result_view_service`**.
  - Toevoeging aan bestaande module (geen aparte `pbs_result_view_service`):
    `result_view_service` is naam-generiek en deze functie hoort er
    natuurlijk in.
  - Bevat: `PBSResultRow` dataclass + `build_pbs_rows(project,
    pbs_results) -> list[PBSResultRow]`. Geen Qt-imports.
  - Veldset `PBSResultRow` (vast):
    - `pbs_id: str`
    - `bouwdeel_naam: str`  *(altijd uit `PBSItem.bouwdeel_naam` als
      single source of truth, ook wanneer `PBSResult` aanwezig is)*
    - `parent_pbs_id: str | None`
    - `level: int`  *(0 = root, oplopend)*
    - `sort_path: tuple[str, ...]`  *(pbs_id-pad van root tot self)*
    - `expected_failures_self: float`
    - `total_downtime_hr_self: float`
    - `total_cost_eur_self: float`
    - `expected_failures_total: float`
    - `total_downtime_hr_total: float`
    - `total_cost_eur_total: float`
    - `unavailability_pct_total: float`  *(recomputed uit
      `total_downtime_hr_total / (config.lifecycle_years × 8760) × 100`)*
  - **DFS-aggregatie**: per knoop `*_total = *_self + Σ children.*_total`
    over alle descendants.
  - **Stable child-volgorde** binnen één parent: alfabetisch op `pbs_id`
    in `build_pbs_rows`. Geen afhankelijkheid op dict-iteratie.
  - **Defensieve handling**:
    - PBS zonder eigen `PBSResult` (puur structurele knoop): `*_self = 0.0`.
    - `parent_pbs_id` wijst naar onbestaand PBS: knoop wordt als root
      behandeld (`level = 0`); geen exception.
    - Cycle in `parent_pbs_id`: gedetecteerd via `visited`-set; betreffende
      knoop wordt als root behandeld; geen exception.
  - **Bewust niet opgenomen**: `total_cm_cost_eur` / `total_pm_cost_eur`
    apart, CM-/PM-downtime apart, `total_risk_contribution`,
    `effect_bijdragen`. Latere slices.

- **Qt-model `PBSResultsTableModel(QAbstractTableModel)`** in
  `rcm_desktop.adapter`.
  - Init: `PBSResultsTableModel(rows: list[PBSResultRow], parent=None)`.
  - 7 kolommen, vaste volgorde:
    1. PBS-id
    2. Bouwdeel  *(DisplayRole = `"  " * level + bouwdeel_naam`,
       UserRole+1 = ráw `bouwdeel_naam`)*
    3. Niveau  *(int)*
    4. Faalmomenten lifecycle (totaal)
    5. Downtime (uur, totaal)
    6. Niet-beschikbaarheid (%, totaal)
    7. Totale kosten (EUR, totaal)
  - `data(index, role=Qt.DisplayRole)`: NL-geformatteerde string
    (kosten met `€`-prefix; floats 2 decimalen; integers zonder
    decimalen; niet-beschikbaarheid met `%`-suffix; Bouwdeel met
    indent-prefix).
  - `data(index, role=Qt.UserRole + 1)`: raw waarden (raw float voor
    sorteerbare numerics; raw int voor Niveau; raw `bouwdeel_naam`
    zonder indent voor schone alfabetische sort op die kolom; raw
    string voor PBS-id).
  - `headerData(...)`: NL-koppen, gecentraliseerd in
    `rcm_desktop.messages`.
  - View koppelt via `QSortFilterProxyModel` met
    `setSortRole(Qt.UserRole + 1)`.

- **UI-plaatsing en default-render**.
  - Nieuw `QGroupBox` "PBS-resultaten" *onder* de bestaande
    `result_table_group` (FM-tabel) in `validate_window`.
  - Bevat één `QTableView` + `QSortFilterProxyModel` +
    `PBSResultsTableModel`.
  - **Default-render = DFS-volgorde, geen actieve sort**: bij elk nieuw
    `done`-result wordt het model gevuld en de header-sort-indicator
    expliciet gewist (`QHeaderView.setSortIndicator(-1, …)` of
    equivalent). `sortByColumn(...)` wordt *niet* aangeroepen.
  - User-klik op een kolomheader schakelt over op flat sort via de
    proxy.
  - **Bewuste asymmetrie met slice 4**: de FM-tabel reset bij elk nieuw
    result naar `sortByColumn(6, Desc)`; de PBS-tabel reset juist naar
    "geen actieve sort". Reden: slice 4 is vlak (kosten desc =
    informatief), slice 5 is hiërarchisch (DFS = informatief).
  - Bij `last_run.status != "done"` of `len(pbs_rows) == 0`: paneel
    verborgen (geen placeholderrij).

- **Forward-compat naar `QTreeView`**.
  - In slice 5: `PBSResultsTableModel(QAbstractTableModel)` op een
    vlakke `list[PBSResultRow]`.
  - Latere slice voegt `PBSResultsTreeModel(QAbstractItemModel)` toe
    die *exact dezelfde* `list[PBSResultRow]`-input consumeert
    (`parent_pbs_id`/`level`/`sort_path` zitten al op de rij). UI swapt
    `QTableView` → `QTreeView` en de modelclass; geen contractwijziging.
  - Latere slice voor PM/CM-uitsplitsing voegt additieve velden toe op
    `PBSResultRow` (`*_cm_*_total`, `*_pm_*_total`); vereist eerst
    kern-uitbreiding van `PBSResult` met `cm_downtime_hr`/`pm_downtime_hr`
    (of een adapter-zijdige rollup vanuit `FMResult`-deelvelden).

- **Reset-discipline** (paneel hidden + model gewist):
  - bij wijziging van het pad-input,
  - bij start van een nieuwe validate-run,
  - bij start van een nieuwe analytische run,
  - bij `run_changed` met `error`-status,
  - bij `run_changed` met `None`.

- **Empty-state**.
  - Tabel zichtbaar uitsluitend bij `last_run.status == "done"` én
    `len(pbs_rows) > 0`.
  - Bij 0 rows: paneel verborgen.

- **AppState**.
  - **Geen** nieuwe velden of signalen in deze slice. De rendering hangt
    op de bestaande `run_changed`-signal en `last_run.pbs_rows`.
  - Bestaande `last_result`/`last_preview`/`last_project`/`last_run` en
    bijbehorende signalen blijven gedragsgelijk aan slice 1/2/3/4.

- **Threading**.
  - Tabel-bouw gebeurt op de werkthread (binnen
    `RunRunner._RunWorker.run`, want het zit in `run_service.run`).
  - UI-thread doet alleen modelupdate + render. Geen extra runner.

- **Architectuurregels** (consistent met `AGENTS.md`):
  - Views importeren uitsluitend uit `rcm_desktop.adapter`,
    `rcm_desktop.messages` en `rcm_desktop.formatting` (typing van
    `rcm_core` waar strikt nodig).
  - Adapter blijft de enige plek met run/orchestratie/Qt-model-logica;
    geen Qt-imports in `rcm_core`.

- **Vocabulaire / messages**.
  - Alle nieuwe NL-strings (groep-titel, kolomheaders) komen in
    `rcm_desktop/messages.py`.
  - Termen: **"faalmomenten"** (niet "falingen"),
    **"niet-beschikbaarheid"** (niet "onbeschikbaarheid").
  - Concreet:
    - `PBS_RESULTS_GROUP_TITLE = "PBS-resultaten"`
    - `PBS_RESULTS_HEADER_PBS_ID = "PBS-id"`
    - `PBS_RESULTS_HEADER_BOUWDEEL_NAAM = "Bouwdeel"`
    - `PBS_RESULTS_HEADER_LEVEL = "Niveau"`
    - `PBS_RESULTS_HEADER_FAALMOMENTEN_TOTAL = "Faalmomenten lifecycle (totaal)"`
    - `PBS_RESULTS_HEADER_DOWNTIME_TOTAL = "Downtime (uur, totaal)"`
    - `PBS_RESULTS_HEADER_UNAVAILABILITY_TOTAL = "Niet-beschikbaarheid (%, totaal)"`
    - `PBS_RESULTS_HEADER_TOTAL_COST_EUR_TOTAL = "Totale kosten (EUR, totaal)"`

- **Issue-split** (vertikaal TDD):
  - **Issue 13** — Pure adapter: `PBSResultRow` + `build_pbs_rows` (DFS,
    aggregatie, recompute, defensieve handling) + `RunResult.pbs_rows`-
    uitbreiding (geen Qt-UI).
  - **Issue 14** — Qt-laag: `PBSResultsTableModel` + `validate_window`-
    integratie (paneel + bedrading + reset + indent-prefix +
    geen-initial-sort + header-indicator-reset). *Blocked by 13.*

## Testing decisions

- **Goede tests**: dekken extern gedrag (input → output, signaalflow,
  reset-gedrag, model-rollen, paneel-zichtbaarheid), niet intern
  Qt-mechanisme of widget-internals.

- **Pure unit-tests** (laag 1, geen Qt):
  - Uitbreiding `tests/test_desktop_result_view_service.py`:
    - `build_pbs_rows_returns_dfs_order_root_to_leaves` (root, child,
      kleinkind in DFS-volgorde; alfabetisch stabiel binnen één parent)
    - `build_pbs_rows_aggregates_self_plus_descendants` voor de drie
      optelbare velden (faalmomenten, downtime, kosten)
    - `build_pbs_rows_recomputes_unavailability_pct_total_from_lifecycle_years`
      (parametrize op meerdere `lifecycle_years`-waarden)
    - `build_pbs_rows_unavailability_pct_total_matches_engine_for_single_leaf`
      (parity-test: single-leaf-PBS zonder kinderen ⇒ recomputed
      `unavailability_pct_total` identiek aan
      `pbs_results[pbs_id].unavailability_pct`)
    - `build_pbs_rows_handles_pbs_without_result_self_zero`
      (parent-only structurele knoop)
    - `build_pbs_rows_handles_missing_parent_as_root`
      (parent_pbs_id wijst nergens heen ⇒ level=0, geen exception)
    - `build_pbs_rows_handles_cycle_without_exception`
      (visited-set; cyclische knoop als root behandeld)
    - `build_pbs_rows_returns_empty_for_empty_input`
    - `build_pbs_rows_assigns_correct_level_and_sort_path`
    - `build_pbs_rows_uses_pbs_item_bouwdeel_naam_as_single_source`
      (ook wanneer `PBSResult.bouwdeel_naam` afwijkt — geen drift)

- **Adapter-integratie** (laag 2, geen Qt):
  - Uitbreiding `tests/test_desktop_run_service.py`:
    - `run_service_happy_path_includes_pbs_rows_with_correct_aggregation`
      (mock op `run_incremental_analysis` met gestubde `pbs_results`-
      dict; assertions op `len(pbs_rows)` en eerste rij)
    - `run_service_precondition_error_returns_empty_pbs_rows`
    - `run_service_internal_error_returns_empty_pbs_rows`
    - regressie: bestaande `rows`/`metrics`/`status`-asserties blijven
      geldig; mode-doorgifte (`full_recompute`, `parallel`) ongewijzigd.

- **Qt-tests** (laag 3, met `pytest.importorskip("PySide6")`):
  - Nieuw `tests/test_desktop_pbs_results_table_model.py`:
    - `rowCount/columnCount` kloppen op gegeven rows.
    - `headerData(orientation, role=Qt.DisplayRole)` levert NL-headers
      uit `messages.py`.
    - `data(index, role=Qt.DisplayRole)` levert NL-geformatteerde
      strings (`"  " * level + bouwdeel`, `format_int/float/eur`,
      `%`-suffix op niet-beschikbaarheid).
    - `data(index, role=Qt.UserRole + 1)` levert raw waarden — incl.
      ráw `bouwdeel_naam` zónder indent.
  - Uitbreiding `tests/test_desktop_qt_flow.py`:
    - na `last_run = done + non-empty pbs_rows` is `pbs_results_group`
      zichtbaar én de eerste rij is de root-PBS (DFS-volgorde, geen
      actieve sort-indicator).
    - na `last_run = done + lege pbs_rows` is paneel verborgen.
    - na `last_run = error` of `path_input.textChanged` is paneel
      verborgen + model leeg.
    - regressie: het FM-tabel-paneel (`result_table_group`) blijft
      zichtbaar bij `done` + non-empty FM-rows; default-sort op
      kosten-totaal-desc voor FM-tabel ongewijzigd.

- **Fixture-strategie**:
  - Edge cases (cycle, missing-parent, missing-PBSResult,
    multi-level-aggregatie) worden afgedekt met **in-memory
    mini-`RCMProject`-instanties**, niet via een fixture op disk.
  - De bestaande `tests/fixtures/sample_project.rcm.json` blijft de
    happy-path-fixture (consistent met slice 4).

- **Prior art**:
  - `tests/test_desktop_result_view_service.py` (slice 4 — pure
    adapter-mapping, in-memory `_fm_result(...)`-helper).
  - `tests/test_desktop_run_service.py` (slice 3 + 4 — adapter-integratie
    tegen `IncrementalRunResult`-stub).
  - `tests/test_desktop_fm_results_table_model.py` (slice 4 — Qt-model-
    rollen, `Qt.UserRole + 1`-trick).
  - `tests/test_desktop_qt_flow.py` (slice 1 t/m 4 — signaalflow,
    paneel-zichtbaarheid, reset-discipline,
    `pytest.importorskip("PySide6")`-skip-strategie).

- **Regressiegate**: volledige `python -m pytest` blijft groen, inclusief
  de geporteerde kerntests en alle slice-1/2/3/4-tests.

## Acceptance criteria

- [ ] `rcm_desktop.adapter.result_view_service` levert nu ook
      `PBSResultRow` en `build_pbs_rows(project, pbs_results)`; geen
      Qt-imports.
- [ ] `RunResult.pbs_rows: list[PBSResultRow]` met default `[]`; happy
      path vult de rijen correct, foutpaden leveren `[]`.
- [ ] `PBSResultRow` bevat exact: `pbs_id`, `bouwdeel_naam`,
      `parent_pbs_id`, `level`, `sort_path`,
      `expected_failures_self/_total`, `total_downtime_hr_self/_total`,
      `total_cost_eur_self/_total`, `unavailability_pct_total`.
- [ ] `build_pbs_rows` retourneert DFS-volgorde, alfabetisch stabiel op
      `pbs_id` binnen één parent; `level` en `sort_path` correct gezet.
- [ ] `build_pbs_rows` aggregeert self + alle descendants voor de drie
      optelbare velden; `unavailability_pct_total` is herberekend uit
      `lifecycle_years × 8760`.
- [ ] `build_pbs_rows` is parity met `pbs_results[pbs_id].unavailability_pct`
      voor een single-leaf-PBS zonder kinderen.
- [ ] `build_pbs_rows` gebruikt `PBSItem.bouwdeel_naam` als single
      source of truth.
- [ ] `build_pbs_rows` handelt PBS zonder `PBSResult` af met `*_self == 0.0`.
- [ ] `build_pbs_rows` handelt missing-parent en cycli defensief af
      (knoop als root, geen exception).
- [ ] `PBSResultsTableModel(QAbstractTableModel)` levert correcte
      `rowCount`, `columnCount`, `headerData`, `data(DisplayRole)` en
      `data(UserRole + 1)`; `Bouwdeel`-DisplayRole heeft indent-prefix,
      UserRole+1 levert raw bouwdeel zonder indent.
- [ ] `validate_window` toont nieuw `QGroupBox` "PBS-resultaten" *onder*
      het FM-tabel-paneel; alleen zichtbaar bij
      `last_run.status == "done"` én `len(pbs_rows) > 0`.
- [ ] Default-render bij elk nieuw `done`-result: DFS-volgorde, geen
      actieve sort-indicator (geen `sortByColumn`-call).
- [ ] User-klik op kolomheader sorteert via `Qt.UserRole + 1` (raw
      numerics).
- [ ] Reset-discipline: tabel hidden + model gewist bij pad-wijziging,
      nieuwe validate, nieuwe run, run-error en `None`.
- [ ] FM-tabel uit slice 4 blijft zichtbaar én default-gesorteerd op
      kosten-totaal-desc bij `done` + non-empty FM-rows (geen
      regressie).
- [ ] Alle nieuwe NL-strings staan gecentraliseerd in
      `rcm_desktop/messages.py`; vocabulaire **"faalmomenten"** en
      **"niet-beschikbaarheid"** wordt consistent gebruikt.
- [ ] Geen views importeren rechtstreeks uit `rcm_core` (behalve typing
      waar strikt nodig).
- [ ] Qt-tests skippen netjes met `pytest.importorskip("PySide6")` als
      `PySide6` niet beschikbaar is.
- [ ] `python -m pytest` is volledig groen.

## Out of scope

**Latere slice — additief uitbreidbaar zonder contractwijziging**:

- `QTreeView` met expand/collapse op de hiërarchie. Vereist alleen
  `PBSResultsTreeModel(QAbstractItemModel)` op dezelfde
  `list[PBSResultRow]`-input.
- Sub-totaal-rij voor "alle wortels" / project-niveau som.
- Cross-table interactie: klik op PBS-rij filtert FM-tabel op alleen
  die PBS (en descendants).
- PM/CM-uitsplitsing op PBS-niveau voor **kosten én downtime**. Vereist
  eerst kern-uitbreiding van `rcm_core.models.PBSResult` met
  `cm_downtime_hr` / `pm_downtime_hr` (of een adapter-zijdige rollup
  vanuit `FMResult.expected_pm_downtime_hr`). Daarna additief op
  `PBSResultRow` met `*_cm_*_total` / `*_pm_*_total`.
- Detail-paneel per PBS-rij (zoom-in op faalwijzen onder die PBS).
- Export naar Excel/CSV van PBS-tabel (en evt. FM).
- Multi-key sorting (bv. eerst level, dan kosten).
- Visuele tree-lijntjes / grafische connectoren.

**Bewust niet (scrub-list of strategische keuze)**:

- Killer/olifant-classificatie of andere RCM1-rangordening
  (`is_unavailability_killer`, `is_cost_elephant`, `classify_results`).
  Geschrapt in RCM2 — zie `CONTEXT.md` + RCM2_REFERENTIE. Niet
  terugbrengen zonder ADR.
- `total_risk_contribution`-kolom (legacy-veld). Symmetrisch met
  slice 4-keuze.
- `effect_bijdragen`-uitsplitsing per effectklasse.
- Volledige i18n via `babel` of `locale.setlocale`. Komt pas wanneer
  meertaligheid daadwerkelijk in scope komt.

**Operationele scope-borgen** (binnen slice 5 maar bewust gekozen):

- Sort-state wordt **niet** gepersisteerd tussen runs — reset naar DFS
  bij elke nieuwe `done`-result.
- Filter/zoekveld op de tabel: niet opgenomen.
- Performance-optimalisatie (cache van geformatteerde strings in
  `PBSResultRow`): niet opgenomen; comment in PRD onder *Comments*.

## Comments

- **Risico — `unavailability_pct`-formule-parity**: onze adapter
  recomputed `unavailability_pct_total = total_downtime_hr_total /
  (config.lifecycle_years × 8760) × 100`. Bij PBS met multipliciteit
  > 1 hanteert de engine mogelijk een andere noemer (effectieve
  multipliciteit × lifecycle_hr). Mitigatie: laag-1-test die parity
  asserteert op een single-leaf-PBS (recomputed waarde moet identiek
  zijn aan `pbs_results[pbs_id].unavailability_pct`). Bij drift wordt
  het een Issue 13-blokkade waarvoor we eerst de engine-formule
  bevestigen.
- **Risico — `bouwdeel_naam`-bron**: voor parent-only-knopen (geen
  eigen `PBSResult`) is `PBSItem.bouwdeel_naam` de enige bron. Wij
  gebruiken **altijd** `PBSItem.bouwdeel_naam` — ook als
  `PBSResult.bouwdeel_naam` aanwezig is — als single source of truth.
  Drift tussen die twee is een validator-onderwerp, niet slice-5.
- **Risico — DFS-volgorde fragiliteit**: dict-iteratie in Python is
  insertion-order, maar tests moeten daar niet op steunen. Wij
  sorteren binnen één parent **alfabetisch op `pbs_id`** in
  `build_pbs_rows`. Expliciet getest op laag 1.
- **Risico — cycle-handling als latente kern-bug**: validator zou cycli
  in `parent_pbs_id` normaal moeten weren. Adapter-defensie
  (visited-set, knoop als root) is een vangnet, geen excuus om
  validator-coverage te negeren. Validator-test is een aparte slice.
- **Risico — performance bij grote fixtures**: `data(DisplayRole)` per
  cel × repaint × format wordt duur bij >1000 PBS-rijen. Voor de
  huidige fixtures geen probleem; bij latere problemen of bij
  toekomstige PM/CM-uitsplitsing (die de kolommen-set verdubbelt) is
  caching of pre-format in `PBSResultRow` een kleine refactor.
- **Risico — locale-onafhankelijkheid**: bewust geen `locale.setlocale`
  gebruikt; de NL-formatter uit slice 4 (`rcm_desktop.formatting`) is
  deterministisch en CI-veilig. Wordt 1-op-1 hergebruikt.
- **Risico — DFS-default vs. user-sort-conflict**: bij elke nieuwe
  `done`-result reset de view de sort-indicator naar "geen actieve
  sort". Als de gebruiker daarna een kolom klikt, blijft die
  sorteer-keuze actief tot de volgende run. Bewuste keuze; expliciet
  getest.
- **Migratie-bijeffect**: deze slice raakt slice 4-FM-tabel niet aan,
  maar voegt een tweede paneel toe in dezelfde window. Expliciete
  regressie-test op laag 3 borgt dat de FM-tabel zichtbaar en
  default-gesorteerd blijft. Geen aanpassing aan slice 4-tests
  verwacht.
