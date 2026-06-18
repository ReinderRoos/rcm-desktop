# PRD — RCM2 desktop slice 58 (werkruimte AFK-seams: pad + rapport)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** Architectuur-verdieping (geen nieuwe eindgebruikersfeatures)  
**Parent:** `/improve-codebase-architecture` + debug rapport-knop (2026-06-03); slice **53** (architectuur-golf); slice **57** (rapportage, afgerond); **ADR-0007** (A/B-slots)  
**Datum:** 2026-06-03  
**GitHub:** https://github.com/ReinderRoos/rcm-desktop/issues/17

## Problem Statement

De **resultatenwerkruimte** heeft na slice **57** werkende rapportgeneratie, maar twee **onderhouds- en vertrouwensproblemen** blijven:

1. **Gesplitste pad-waarheid** — `ProjectSession.path` kan `None` zijn terwijl het project wél geladen is en een analyse heeft gedraaid (pad alleen in het UI-veld). Rapport (en andere flows) stopten stil of faalden inconsistent; de hotfix zit nog in de view (`_project_file_path`), niet achter een geteste adapter-**seam**.
2. **Verspreide rapport-beslissingen** — Of een rapport kan (`assess_report_eligibility`), welke runs in het rapport komen (`resolve_report_run_bundle`), en dialoog-preview gebruiken overlappende regels en een **shallow** alias (`resolve_bundle_for_preview`). Toolbar, dialoog en toekomstige callers kunnen uit sync raken zonder dat tests dat vangen.

Ontwikkelaars willen **kleine, AFK-verifieerbare** stappen (pytest, geen handmatige UI-regressie) met **grote hefboom**: minder stille failures, één waarheid voor pad en rapport-gating. Dit is bewust **niet** de grote venster-splitsing uit slice 53.

## Solution

Lever drie **diepe, Qt-vrije modules** (of uitbreidingen) in vaste volgorde, elk mergebaar met pytest als gate:

| Stap | Module | Leverage |
|------|--------|----------|
| **1** | **Rapport-werkruimte-entry** | Eén call levert `{eligible, reason, bundle}`; verwijder pass-through alias |
| **2** | **Projectpad-resolutie** | Eén call levert schijfpad + afgeleide paden (cache, rapport-default); view leest alleen adapter |
| **3** | **Regressietests** | Vastleggen pad-fallback en rapport-entry; optioneel import-guard uitbreiden |
| **4 (optioneel)** | **Split-layout opruiming** | Constanten + compare-split op één plek; legacy stub zonder productie-gebruik |

Geen wijziging aan rapportinhoud, PDF-pipeline of A/B-semantiek (slice 56/57).

## User Stories

### Coördinatie

1. Als **product owner** wil ik slice **58** als kleine AFK-golf naast slice **53**, zodat agents niet het volledige venster hoeven te splitsen voor stabiliteit.
2. Als **ontwikkelaar** wil ik **vaste PR-volgorde** (pad-entry → rapport-entry → tests → optioneel split), zodat elke merge klein en reviewbaar blijft.
3. Als **ontwikkelaar** wil ik dat elke stap **alleen pytest** als acceptatie gebruikt, zodat ik weinig handmatig hoef te klikken.

### Rapport-werkruimte-entry (stap 1)

4. Als **ontwikkelaar** wil ik **één functie** die eligibility en `ReportRunBundle` samen oplost, zodat toolbar en dialoog dezelfde waarheid gebruiken.
5. Als **ontwikkelaar** wil ik **`resolve_bundle_for_preview` verwijderd** of intern gemaakt, zodat geen shallow alias de codebase vervuilt.
6. Als **analist** wil ik dat de rapportknop **enabled** blijft wanneer de bundle bestaat, zodat UX consistent is met de dialoog-preview.
7. Als **analist** wil ik bij geen bundle een **duidelijke reason** (bestaande message constants), zodat stil falen niet terugkomt.
8. Als **ontwikkelaar** wil ik dat **compare A-only** en **A+B** dezelfde prioriteit houden als slice **57**, zodat geen regressie in A/B-workflows.
9. Als **ontwikkelaar** wil ik dat **live `PlanningOverlayState`** alleen voor single-run bundle-resolutie wordt gebruikt, zodat ADR-0007 (bevroren slot-overlays in compare) intact blijft.

### Projectpad-resolutie (stap 2)

10. Als **ontwikkelaar** wil ik **`resolve_project_file_path(session, path_text)`** in de adapter, zodat de view geen pad-beleid dupliceert.
11. Als **analist** wil ik **rapport genereren** kunnen wanneer het pad in het UI-veld staat maar `ProjectSession.path` leeg is, zodat het gedrag van de debug-fix permanent en getest is.
12. Als **ontwikkelaar** wil ik bij **geen pad** een bestaande melding (`ERROR_EMPTY_PATH`), zodat de gebruiker weet wat te doen.
13. Als **ontwikkelaar** wil ik optioneel **`cache_path`** en **`default_report_dir`** op hetzelfde resolved object, zodat run/presentatie/rapport hetzelfde pad-**interface** delen (smalle scope: rapport + minstens één andere caller in dezelfde PR of direct erna).
14. Als **ontwikkelaar** wil ik dat **`AppState._sync_project_session`** ongewijzigd blijft in v1, zodat geen brede state-migratie nodig is.

### Regressietests (stap 3)

15. Als **ontwikkelaar** wil ik **tabeltests** voor pad-resolutie (session.path / path_text / beide leeg), zodat edge cases AFK gedekt zijn.
16. Als **ontwikkelaar** wil ik tests dat **`assess_report_workspace`** eligibility en bundle consistent teruggeeft, zodat toolbar/dialoog niet divergeren.
17. Als **ontwikkelaar** wil ik een **lichte pytest-qt smoke** dat rapport-dialoog opent wanneer alleen `path_input` gevuld is, zodat de productie-bug niet terugkomt.
18. Als **ontwikkelaar** wil ik de bestaande slice **57** rapport-tests groen houden, zodat materialisatie/docx niet regresseren.

### Optioneel: split-layout (stap 4)

19. Als **ontwikkelaar** wil ik **split-constanten** op één plek, zodat ADR-0006/0007 niet verward worden met twee modules.
20. Als **ontwikkelaar** wil ik dat **productie** alleen `compare_split_layout` gebruikt, zodat `workspace_split_layout` geen no-op orchestrator meer is.
21. Als **ontwikkelaar** wil ik dat **slice 53 issue 07** tests (`workspace_split_layout` niet in view) groen blijven, zodat legacy-opruiming de golf niet blokkeert.

### Niet-functioneel

22. Als **auditor** wil ik dat wijzigingen **geen nieuwe product-UI** introduceren, zodat scope beheersbaar blijft.
23. Als **ontwikkelaar** wil ik **geen `rcm_core`-wijzigingen**, zodat motor en domeinmodel onaangetast blijven.
24. Als **ontwikkelaar** wil ik **Nederlandse copy** via bestaande message constants, zodat geen losse strings in de view bijkomen.

## Implementation Decisions

### Modules (bouwen/wijzigen)

| Module | Actie | Diepte |
|--------|-------|--------|
| **Rapport-werkruimte-entry** | Uitbreiden `report_eligibility_service` of nieuw `report_workspace_service` | **Diep**: één entry `assess_report_workspace(last_run, compare_slots, live_overlay) -> ReportWorkspaceAssessment` met `eligible`, `reason`, `bundle \| None` |
| **Rapport-run-bron** | `report_run_source_service` blijft SSOT voor bundle-samenstelling | Ongewijzigde **interface**; entry module delegeert |
| **Projectpad-resolutie** | Nieuw `project_path_resolution_service` (of `workspace_path_service`) | **Diep**: `ResolvedProjectPath` frozen dataclass: `file_path \| None`, helpers `cache_path()`, `default_report_output_path(project)` |
| **Resultatenwerkruimte-view** | Dunner: roept adapter-entry aan; `_project_file_path` verwijderen | Alleen Qt-bind en `QMessageBox` |
| **Rapport-generatie-dialoog** | Gebruikt rapport-entry i.p.v. drie× losse resolve | Geen eigen bundle-regels |
| **Split-layout (optioneel)** | `compare_split_layout_service` + constanten; deprecate stub in `workspace_split_layout` | Consolidatie, geen UX-wijziging |

### Interfaces (beslissingsvorm)

**ReportWorkspaceAssessment** (conceptueel):

```python
@dataclass(frozen=True)
class ReportWorkspaceAssessment:
    eligible: bool
    reason: str  # leeg indien eligible
    bundle: ReportRunBundle | None
```

**ResolvedProjectPath**:

```python
@dataclass(frozen=True)
class ResolvedProjectPath:
    file_path: Path | None

def resolve_project_file_path(
    *,
    session_path: Path | None,
    path_text: str,
) -> ResolvedProjectPath: ...
```

Prioriteit: `session_path` → niet-lege `path_text` → `None`.

### Volgorde en grenzen

- **PR1:** Rapport-entry + callers (toolbar, dialoog, preview counts); alias weg.
- **PR2:** Pad-resolutie + rapport/run callers die nu pad uit view halen (minimaal rapport; bij voorkeur ook presentatie-cache start als ≤20 regels diff).
- **PR3:** Tests + pytest-qt smoke.
- **PR4 (optioneel):** Split-layout alleen als PR1–3 groen en geen open slice-53-conflict.

### ADR- en slice-relaties

- **ADR-0007:** Bundle uit `CompareSlotState`; geen wijziging aan bevroren overlay-semantiek.
- **ADR-0006:** Geen legacy scenario-compare in werkruimte; stap 4 versterkt alleen opruiming.
- **Slice 57:** Rapportmaterialisatie, docx, PDF blijven buiten scope.
- **Slice 53:** Geen orchestrator-golf of venster-split in deze slice.

### Wat niet in de view blijft

- Geen duplicate eligibility-check naast adapter-entry.
- Geen stille `return` bij ontbrekend pad zonder `QMessageBox`.

## Testing Decisions

### Wat is een goede test

- Test **extern gedrag** van de adapter-**interface**: gegeven run/slot/pad-input → eligibility, bundle, resolved path.
- Geen asserts op private helpers of call-volgorde in de view.
- pytest-qt alleen voor “dialoog opent / knop enabled” smokes; bulk via unit tests.

### Modules met tests (verplicht)

| Module | Testbestand (nieuw/uitbreiden) | Prior art |
|--------|-------------------------------|-----------|
| Rapport-werkruimte-entry | `test_report_workspace_assessment.py` of uitbreiding `test_report_eligibility_service.py` | `test_report_eligibility_service.py`, slice 57 |
| Projectpad-resolutie | `test_project_path_resolution_service.py` | Patroon `test_report_path_service.py` |
| View smoke | `test_slice58_workspace_path_report_smoke.py` | `test_slice57_workspace_report_smoke.py` |
| Split (optioneel) | bestaande `test_compare_split_layout_service.py` | `test_slice53_issue07_legacy_pr7a.py` |

### CI-gate (AFK)

Na elke PR minimaal:

```text
python -m pytest tests/test_report_*.py tests/test_slice57_*.py tests/test_slice58_*.py tests/test_architecture_deepening.py -q
```

Optioneel PR4: `tests/test_compare_split_layout_service.py tests/test_slice29_scenario_ui_deprecation.py`

### Handmatig (minimaal)

- Eén keer na PR2: rapport genereren met project alleen via pad-veld (sanity). Geen LibreOffice vereist voor acceptatie.

## Out of Scope

- Monolithische `ResultsWorkspaceWindow` splitsen (slice 53 orchestrator-golf).
- `workspace_session_service` volledig verwijderen of `ResultsWorkspaceController` uitbreiden tot volledige post-run pipeline.
- Meekoppel-workflow extractie (slice 54/55).
- Wijzigingen aan rapportinhoud, drempels, PDF/LibreOffice, narrative templates.
- Nieuwe KPI’s, extra rapportsecties, ValidateWindow-rapportknop.
- `AppState` herschrijven zodat `ProjectSession.path` altijd gezet is (kan later; niet nodig voor deze slice).
- Runner-consolidatie (`BackgroundRunner` templates).
- Meertaligheid of branding in rapporten.

## Further Notes

- **Bug-achtergrond (2026-06-03):** Logs toonden `early exit: no session/path` met `session_none: false` → `session.path` was `None`, pad stond in `path_input`. Fix hoort in adapter + tests, niet alleen in de view.
- **Aanbevolen agent-volgorde:** PR1 → PR2 → PR3 → (optioneel) PR4; geen parallelle PRs op dezelfde view-methoden.
- **Module-check (skill):** Bevestig vóór implementatie of `report_workspace_service` apart moet of `report_eligibility_service` uitgebreid wordt; default: **uitbreiden eligibility module** om bestandsgolf klein te houden.
- **Tests:** Alle drie adapter-modules uit de tabel hebben unit tests; view alleen smoke.
