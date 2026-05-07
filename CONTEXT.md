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
`bibliotheek-*`. Bewust geen `serve`, geen Excel-IO, geen Monte Carlo.

**Adapter Qt** (`rcm_desktop.adapter`)
Qt-zijdige run-orchestratie en model/view-bindings.

## Wat ontbreekt t.o.v. RCM1 (bewust)

- **Killer/olifant-classificatie** is verwijderd. `PBSResult` heeft geen
  `is_unavailability_killer`/`is_cost_elephant`. Geen `classify_results`.
  Gebruikers leiden rangordening zelf af uit `total_cost_eur`,
  `total_downtime_hr`, `unavailability_pct`. Zie supersedes-ADR.
- Streamlit-shell, runflow-contract, dashboard-modules: niet geporteerd; UI
  wordt opnieuw opgebouwd in PySide6.
- Excel-IO, Monte Carlo, LTAP-light, meekoppelkansen: buiten scope tracer-bullet.
