# RCM2 desktop — domeinvocabulaire

Deze repo is de native desktop-variant (PySide6/Qt6) van RCM, gestart als fresh
copy-and-adapt van de RCM1-kern. Vocabulaire dat domein-experts en agents nodig
hebben om eenduidig te praten:

## Language

**Domain model (`rcm_core.models`)**
De canonieke dataclasses (`RCMProject`, `PBSItem`, `Faalwijze`, `PMTask`,
`EffectKlasse`, `FMResult`, `PBSResult`) en hun `to_dict()`/`from_dict()`. Bron
voor analytische run en serialisatie.

**Editing schema registry (`rcm_core.editing.schemas.ENTITY_SCHEMAS`)**
Bewuste tweede bron voor bewerkbare entiteiten in de UI: titels, `store_key`,
welke velden zichtbaar zijn, `field_types` (string-coerciion), `required_fields`,
en `fk_rules` voor validatie. Niet automatisch uit `models` gegenereerd.

**FK target (schema-backed)**
FK in `fk_rules` waarvan het doel óók in `ENTITY_SCHEMAS` staat. Geldige waarden
komen uit de in-memory edit-buffer voor die entiteit.

**FK target (project-backed)**
FK-doel zonder eigen rij in `ENTITY_SCHEMAS` (bv. `functies`, `task_groups`).
Geldige IDs komen uit `RCMProject` (zie `rcm_core.editing.validation.resolve_fk_set`).

**Tabulaire editing-pipeline**
De keten **initialiseren → bewerken (buffers) → valideren → materialiseren →
persist (disk) of run (analyse)**. Canoniek model in de UI-sessie zit onder
`rcm_core.editing.pipeline.CANONICAL_PROJECT_KEY`. Sessie is **injecteerbaar**:
`init_edit_state`, `apply_rows`, `validate_all_entities`, `build_project_from_state`
accepteren optioneel `session=dict`. In RCM2 is die injectie **verplicht** vanuit
`rcm_desktop.adapter` — geen Streamlit-`session_state`-aanname meer.

## Cache + run

**Globale digest** (`rcm_core.cache.compute_global_digest`)
Vingerafdruk over volledige canonieke `RCMProject.to_dict()` + `CACHE_INPUTS_VERSION`.
Bij mismatch: cache niet vertrouwen voor incrementele merge → alle faalwijzen opnieuw.

**FM-invoerhash** (`rcm_core.cache.compute_fm_hash`)
SHA256 over canonieke JSON-slice van de FM-relevante invoer (FM, gekoppeld PBS,
PM-taken, alle `task_groups`, volledige `config`, FM/PM-effectlinks, volledige
`pbs_items` voor effectieve leeftijd/multipliciteit).

**Run-orchestratie** (`rcm_core.incremental_run.run_incremental_analysis`)
Eén pad voor volledige en incrementele analytische run op een geladen `RCMProject`.
Combineert cache-seam met motor (`rcm_core.engine`).

**Adapter CLI** (`rcm_core.cli`)
Rookproef-tool boven de kern; subcommando's `validate`, `impact`, `run`, `fit`,
`bibliotheek-*`. Bewust geen `serve`, geen Monte Carlo in CLI. Excel **import**
alleen via desktop/adapter (ADR-0004), geen Excel in `rcm_core.cli`.

**Adapter Qt** (`rcm_desktop.adapter`)
Qt-zijdige run-orchestratie en model/view-bindings.

## FM-verificatie & spot-check

Drie lagen om **één faalwijze (FM)** te controleren — van streng naar interactief:

1. **pytest / CLI** — Strengste, reproduceerbare verificatie. Gebruik fixtures en
   motor-`FMResult` (inclusief `horizon_profile` waar aanwezig), reconcile-tests
   (`tests/test_nmf_schedule.py`, adapter unit-tests). Leg regressies hier vast
   vóór je in de UI kijkt.

2. **Resultatenwerkruimte, modus FM-detail** — Standaard interactief pad na slice 34.
   - **Verifiëren (read-only):** selecteer één FM; het **inspectorpaneel** toont
     lifecycle-totalen, jaarreeks uit `horizon_profile` (faalmomenten-proxy,
     correctief EUR, downtime, verborgen NB), reconcile-status en **FM-invoerhash**.
     Zie `fm_verification_service` en
     `.scratch/rcm-desktop-slice34-fm-verificatie-werkruimte/`.
   - **Bewerken (slice 44):** **dubbelklik** op een FM-rij opent de modale
     **faalwijze-editor** (`FmEditorDialog`): basis (faaltype, MTTF, NMF, startleeftijd
     via PBS-`bouwjaar`), effecten, correctief (CM-split materiaal/arbeid, hersteltijd),
     preventief (PM-taken, taakgroepen, PM-effectlinks). **OK** valideert via de
     tabulaire editing-pipeline, werkt het project bij en triggert een
     **incrementele run** (`full_recompute=False`) — geen volledige herberekening.
     Waarschuwingen bij gedeeld PBS of gedeelde taakgroep. PRD/issues:
     `.scratch/rcm-desktop-slice44-fm-bewerken-werkruimte/`.

3. **Legacy ValidateWindow** (`--legacy-validate` / `RCM_LEGACY_VALIDATE=1`) —
   **Projectcockpit** voor smalle faalwijzen-grid-bewerking, valideren, run en
   LTAP/PM what-if — **niet** het primaire pad voor volledige FM-bewerking (slice 44).
   Layout-cleanup (slice 8) is uitgesteld.

Kalenderjaar in de inspector gebruikt dezelfde mapping als LCC/Tijdsplot:
`modeljaar` + horizonindex. Jaar-faalmomenten in de UI zijn **presentatie-proxy**
(zelfde pad als Top 10/LCC), geen tweede motorberekening.

## Wat ontbreekt t.o.v. RCM1 (bewust)

- **Killer/olifant-classificatie** is verwijderd. `PBSResult` heeft geen
  `is_unavailability_killer`/`is_cost_elephant`. Geen `classify_results`.
  Gebruikers leiden rangordening zelf af uit `total_cost_eur`,
  `total_downtime_hr`, `unavailability_pct`. Zie supersedes-ADR.
- Streamlit-shell, runflow-contract, dashboard-modules: niet geporteerd; UI
  wordt opnieuw opgebouwd in PySide6.
- **RCM-Cost import (bootstrap):** RCM-Cost export → `.rcm.json` via de
  resultatenwerkruimte (ADR-0004). Geen gevolgkosten-import; PM-effectlinks alleen
  volgens PM-spike. Subset-export terug naar Availability Workbench is latere slice.
- Monte Carlo UI/motor, LTAP-light: buiten scope tracer-bullet.
- Meekoppelkansen: toegestaan via **ADR-0005** (adapter-only in resultatenwerkruimte LCC+what-if); geen scrub-list-port van RCM1-module; `ltap_light` blijft out.
