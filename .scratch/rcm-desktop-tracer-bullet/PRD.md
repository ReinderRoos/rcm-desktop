# PRD — RCM2 desktop tracer-bullet (eerste milestone)

**Status:** ready-for-agent
**Versie:** 1.0
**Triage-labels:** zie `../../AGENTS.md`

## Bron / context

- `../../../rcm/.scratch/rcm2-restart-reference/RCM2_REFERENTIE.md` (alle
  strategische beslissingen).
- `../../docs/adr/ADR-0001-python-only-ui-blauwdruk-geparkeerd.md`
- `../../docs/adr/ADR-0002-pyside6-ui-framework.md`
- `../../docs/adr/ADR-0003-killer-olifant-uit-domain-model.md`

## Problem statement

RCM2 desktop start als greenfield-repo met een geporteerde RCM1-kern. Voor er
breed gebouwd wordt moet bewezen worden dat de hele keten **fixture inladen
→ faalwijzes bewerken → run uitvoeren → Top-X tonen** in PySide6 werkt op de
gepoorte kern. Dit is de tracer-bullet en de eerste validatie van de
RCM2-architectuur.

## Solution

Een minimale verticale slice door de keten:

1. **Smoke-stage** — kern werkt los van Qt: `python -m rcm_core.cli validate`
   en `... run --full` op de awzi-fixture geven verwachte output.
2. **Qt-skeleton** — `QApplication` met `QMainWindow`, één tab/pagina.
3. **Faalwijze-tabel** — `QTableView` + `QAbstractTableModel` boven
   `rcm_core.editing.state` (subset velden: MTTF, sigma, `functie_id`-FK,
   PBS-FK), met validatiehighlight per cel. Andere entiteiten read-only.
4. **Run-thread** — knop "Bereken" start `incremental_run.run_incremental_analysis`
   op een `QThread`; voortgang via signaal.
5. **Top-X-resultaatscherm** — `QTableView` met PBS-resultaten gesorteerd op
   kosten of niet-beschikbaarheid (geen labels).

Buiten scope: PBS-tree, dashboard, drilldown, scenario CM/PM, Excel-import,
disk-save, multi-user.

## User stories

1. Als analist wil ik de awzi-fixture in één klik laden, zodat ik direct kan
   bewerken en rekenen.
2. Als analist wil ik MTTF/sigma/`functie_id`/PBS van een faalwijze wijzigen
   in een tabel met directe validatiefeedback per cel.
3. Als analist wil ik op "Bereken" klikken en zien dat de run draait zonder
   dat het venster bevriest.
4. Als analist wil ik na de run een Top-X-tabel zien met PBS-bijdragen,
   sorteerbaar op `total_cost_eur` of `unavailability_pct`.
5. Als ontwikkelaar wil ik dat de adapterlaag tussen kern en Qt los testbaar
   is met `pytest-qt`, zodat decoupling daadwerkelijk werkt.

## Implementation decisions

- **TDD**: verplicht in `rcm_desktop/adapter/` (Qt-models, run-runner,
  signal-bridges). Geen TDD voor `rcm_desktop/views/` (visueel testen).
- **Signals/slots**: alle communicatie tussen views en adapter via signalen,
  niet via directe attribuut-toegang. Maakt testen via `qtbot` mogelijk.
- **Session injectie**: editing-state krijgt een gewone `dict` als session,
  niet Streamlit's `session_state`. Dit fixeert UI/kern-decoupling.
- **Geen klasse-erfenissen op `editing/state.py`**: adapter-Qt-models houden
  een referentie naar de `dict`-session en spiegelen wijzigingen via
  `apply_rows`/`validate_all_entities`.
- **Run-thread**: één `RunController(QObject)` met signalen `started`,
  `progress(affected_count, total)`, `finished(IncrementalRunResult)`,
  `failed(Exception)`. Worker draait `run_incremental_analysis` in `QRunnable`
  of dedicated `QThread`.
- **Top-X-presentatie**: `RankedPBSTableModel` exposeert PBS-resultaten met
  configureerbare sortkolom (kosten / niet-beschikbaarheid).

## Testing decisions

- Bestaande pytest-suite (geporteerd uit RCM1, scrub-list toegepast) MOET groen
  blijven en is de eerste vangnetcheck.
- Nieuwe tests in `tests/` voor adapter-classes met `pytest-qt`:
  `qtbot.waitSignal(...)` op `started`/`finished`, model-data-asserts op
  `QAbstractTableModel.data(index, role)`, validatie-cellkleur via Qt-rol.
- Geen UI-rendering-tests; smoke-test op `python -m rcm_desktop.main` is
  voldoende.

## Acceptance criteria (tracer-bullet)

- [ ] CLI smoke: `validate` en `run --full` op awzi-fixture geven exit 0 en
      verwachte output.
- [ ] Pytest groen (alle gepoorte tests + nieuwe adapter-tests).
- [ ] Qt-app start, toont faalwijzentabel boven awzi-fixture, accepteert edits
      met validatiefeedback.
- [ ] Run-knop draait incremental analyse op QThread zonder UI te bevriezen.
- [ ] Top-X-tabel toont PBS-bijdragen na run; sortering werkt.
- [ ] Eerste edit → run → Top-X-shift is zichtbaar (FM-invoerhash werkt).

## Out of scope

- Save/load (in-memory tijdens tracer).
- PBS-tree (`QTreeView`), drilldown, dashboard.
- Scenario CM vs PM, per-jaar weergave.
- Multi-user, server-deploy.
- PyInstaller-bundle (volgt latere milestone).
- Excel-import/export.

## Comments
