# Kanban-handoff — slice 39 meekoppelkansen Planning-2a (2026-05-22)

**Repo:** `rcm-desktop`  
**Slice-map:** `.scratch/rcm-desktop-slice39-meekoppelkansen-planning-2a/`  
**ADR:** `docs/adr/ADR-0005-meekoppelen-onderhoud.md`

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
python -m pytest tests/test_meekoppelkansen_discovery_service.py `
  tests/test_meekoppel_apply_service.py tests/test_desktop_meekoppel_workspace.py -q
```

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

*Laatst bijgewerkt: 2026-05-22 — slice 39 issues 01–04.*
