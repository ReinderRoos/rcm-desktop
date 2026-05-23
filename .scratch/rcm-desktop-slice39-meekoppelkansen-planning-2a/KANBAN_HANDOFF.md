# Kanban-handoff — slice 39 meekoppelkansen Planning-2a (2026-05-22)

**Doel:** Vastlegging voor vervolgsessie. Lees dit bestand + `PRD.md` + `docs/adr/ADR-0005-meekoppelen-onderhoud.md` vóór je verder gaat.

**Repo:** `rcm-desktop`  
**Slice-map:** `.scratch/rcm-desktop-slice39-meekoppelkansen-planning-2a/`  
**ADR:** `docs/adr/ADR-0005-meekoppelen-onderhoud.md`  
**Parent:** slice 28–30 (what-if overlay), slice 38 (LCC render-cache)  
**Referentie-fixture:** `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`

---

## Kanban-status (issues)

| # | Titel | Triage | Opmerking |
|---|--------|--------|-----------|
| 01 | ADR-0005 + CONTEXT scrub-list | **done** | Geen runtime-code |
| 02 | Read-only discovery + paneel | **done** | `meekoppelkansen_discovery_service` |
| 03 | Preview + apply overlay-shift | **done** | `meekoppel_apply_service` |
| 04 | Venster N, anker, smoke + handoff | **done** | UI spinbox; pytest-qt |

**Slice status:** tracer-bullet **af** (gate 2a→2b: handmatige Haarlem-checklist).

---

## Wat werkt

1. LCC + **what-if aan** → paneel **Meekoppelkansen** met REV-paren (zelfde `element_naam`, Δ ≤ N).
2. **Preview** met anker vroegste/laatste due-jaar; **Toepassen** = overlay-shift (geen motor-run).
3. Venster **N** (1–5, default 2) ververst suggesties.
4. What-if uit → paneel toont hint; apply/preview disabled.

### Tests

```powershell
cd rcm-desktop
.\.venv\Scripts\Activate.ps1
python -m pytest tests/test_meekoppelkansen_discovery_service.py `
  tests/test_meekoppel_apply_service.py tests/test_desktop_meekoppel_workspace.py -q
```

**Laatste run (2026-05-23):** **13 passed** (12.9s).

**Sessie-start checklist (agent):**

1. Lees ADR-0005 (scope 2a/2b/2c, geen motor-run, geen ltap_light).
2. Draai bovenstaande pytest-subset — moet groen zijn vóór UI-werk.
3. Code-pad: discovery → preview/apply → `ResultsWorkspaceWindow` meekoppel-paneel (alleen LCC + what-if).
4. **Niet starten met slice 40** tot Haarlem-handchecklist hieronder groen is.

---

## Handmatige Haarlem-checklist (gate 2a→2b)

Fixture: `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`

1. Run → LCC → what-if aan → meekoppelkansen-paneel zichtbaar.
2. Wijzig venster N → lijst verandert waar verwacht.
3. Selecteer suggestie → Preview → shift-samenvatting klopt.
4. Toepassen → overlay-teller stijgt; LCC-curve/jaardetail vernieuwt.
5. Reset overlay → baseline; suggesties opnieuw consistent.
6. Geen regressie: handmatige shift in jaardetail, slice 36–38 LCC snelheid.

---

## Belangrijkste bestanden

| Pad | Rol |
|-----|-----|
| `docs/adr/ADR-0005-meekoppelen-onderhoud.md` | Bindende besluiten |
| `rcm_desktop/adapter/meekoppelkansen_discovery_service.py` | Discovery |
| `rcm_desktop/adapter/meekoppel_apply_service.py` | Preview + apply bridge |
| `rcm_desktop/adapter/meekoppel_suggestions_table_model.py` | Tabelmodel |
| `rcm_desktop/views/results_workspace_window.py` | LCC-paneel |

---

## ADR-0005 samenvatting (bindend)

| Onderwerp | Besluit |
|-----------|---------|
| **2a (slice 39)** | REV-paren,zelfde `element_naam`, \|Δjaar\| ≤ N (default 2); discovery + preview + opt-in apply |
| **Apply** | Alleen overlay (`apply_overlay_shift`); geen motor-run; geen `.rcm.json`-mutatie |
| **Kosten** | Geen `ltap_light`-korting bij expliciet meekoppelen |
| **UI** | Alleen resultatenwerkruimte, modus LCC, what-if aan |
| **2b (slice 40)** | PBS-bundeling alle REV per element — **na** groene Haarlem-gate |
| **2c** | Functioneel meekoppelen — spike + go/no-go |

Zie `docs/adr/ADR-0005-meekoppelen-onderhoud.md` voor volledige tekst.

## Volgende stap (mens / product)

- **Gate 2a→2b:** handmatige Haarlem-checklist (sectie hierboven) — enige openstaande exit voor slice 39.
- **Daarna:** slice 40 PRD/issues (Planning-2b PBS-bundeling).

---

*Laatst bijgewerkt: 2026-05-23 — sessie-start; CI-subset 13/13 groen; gate Haarlem nog open.*
