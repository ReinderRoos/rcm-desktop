# PRD — Meekoppel preview-inzicht & bundel-scope (slice 54, issue 03b)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** UX-inzicht + adapter-contract (meekoppel preview)  
**Parent:** `.scratch/rcm-desktop-slice54-meekoppel-workflow-seam/PRD.md` (v0.2+)  
**Bron:** grill-me preview-inzicht (2026-06-02); gebruikersincident HWP-IN (verschil 0 vs doel 2047)  
**Datum:** 2026-06-02

## Problem Statement

Een reliability-analist die meekoppelkansen gebruikt, ziet in de locatietabel vaak **“Verschil (baseline) = 0”** en tooltips met alleen **baseline**-eerste-uitvoeringsjaren, terwijl **Preview** op basis van **effectieve** jaren (inclusief what-if-overlay) een ander doeljaar en grote verschuivingen toont (bijv. alles naar jaar 21 ≈ 2047).

Zonder speurwerk is niet te beantwoorden:

1. **Bundel-scope** — geldt preview voor de geselecteerde locatierij (bijv. 16 REV) of de hele PBS-selectie (bijv. 63 REV)?
2. **Anker/trekker** — welke taak(ten) bepalen het doeljaar bij “bundel naar laatste/vroegste”?
3. **Jaarsoort** — wat is baseline versus effectief, en wat is de delta naar het doel?

Dat leidt tot verkeerde mentale modellen (“ze zijn toch al gebundeld?”) en vertrouwensschade vóór apply. Het probleem is urgent omdat apply overlay-mutaties doet (ADR-0005: voorstel-first); de analist moet **vóór** toepassen in seconden kunnen verklaren wat er gebeurt.

## Solution

Lever een **preview-inzicht-pakket** in de v2-selectiedialoog (`meekoppel_workflow_v2`), dat scope, trekker en jaarsoorten expliciet maakt:

1. **Hybride bundel-scope** bij openen: één locatierij geselecteerd → preview op die groep; anders hele PBS-selectie — altijd zichtbaar in een vaste scope-regel in de dialoog-header.
2. **Scope-wissel in de dialoog** tussen locatierij en PBS-selectie met herberekening, reset van checkbox-selectie naar default in de nieuwe scope, en korte melding.
3. **Trekker-regel** “Bepaald door …” (altijd zichtbaar; bij gelijkstand alle trekkers of “N taken op jaar X”).
4. **Preview-tabel** met kolommen Baseline | Effectief | Doel | Δ (Δ = effectief → doel), trekkers bovenaan en visueel gemarkeerd.
5. **Locatietabel buiten preview:** kolomkoppen verduidelijken als baseline; tooltip per REV met baseline · effectief wanneer what-if actief is.
6. **Apply-contract:** strikt WYSIWYG (actieve scope ∩ aangevinkte taken, zelfde anker) plus korte bevestiging vóór toepassen.

Legacy tekst-`QMessageBox`-preview blijft ongewijzigd tot flag-sunset.

## User Stories

1. As a reliability-analist, I want to see which REV-set the preview bundles (locatierij vs PBS-selectie), so that I do not confuse 16 tasks with 63.
2. As a reliability-analist, I want the default preview scope to match my table selection when one location row is active, so that “verschil 0” on that row is evaluated in the right context.
3. As a reliability-analist, I want the default preview scope to fall back to my full PBS selection when no single row is selected, so that multi-select workflows still work.
4. As a reliability-analist, I want a persistent scope line in the preview header, so that I never have to guess the active bundle scope.
5. As a reliability-analist, I want to switch scope inside the preview dialog (row ↔ PBS) without closing and reopening, so that I can compare “this row only” vs “whole selection” quickly.
6. As a reliability-analist, I want scope switches to recalculate target year, drivers, and table rows immediately, so that the preview stays truthful.
7. As a reliability-analist, I want checkbox selection to reset to all shiftable tasks when scope changes, so that old ticks do not mislead after a scope change.
8. As a reliability-analist, I want a short notice when scope change resets selection, so that the reset feels intentional not buggy.
9. As a reliability-analist, I want a line “Determined by …” naming the task(s) that set the target year, so that I know why the target is 2047 and not 2028.
10. As a reliability-analist, I want multiple drivers listed when several tasks share the max effective year, so that no arbitrary single task is hidden.
11. As a reliability-analist, I want a clear message when all tasks already sit on the target year, so that I understand a no-shift preview.
12. As a reliability-analist, I want separate Baseline and Effective columns per task, so that I see overlay shifts without opening tooltips.
13. As a reliability-analist, I want Target and Delta columns computed from effective → target, so that numbers match what apply will do.
14. As a reliability-analist, I want target-driver rows sorted to the top of the preview table, so that I find the decisive tasks without scrolling.
15. As a reliability-analist, I want target-driver rows visually marked (icon or background), so that they stand out in long lists.
16. As a reliability-analist, I want location table headers to say they show baseline years, so that “verschil 0” is not read as “already bundled in what-if”.
17. As a reliability-analist, I want row tooltips to show baseline and effective per REV when what-if is on, so that I can sanity-check before opening preview.
18. As a reliability-analist, I want tooltips to stay lightweight (only visible row tasks, no motor run), so that the panel stays responsive.
19. As a reliability-analist, I want apply to affect exactly the checked tasks in the active scope with the shown anchor, so that preview and apply never diverge (WYSIWYG).
20. As a reliability-analist, I want a brief confirmation before apply stating scope and count, so that I do not accidentally apply a broader set than I reviewed.
21. As a developer, I want scope, drivers, and summary text computed in the adapter preview contract, so that the view only renders and stays thin.
22. As a developer, I want preview insight covered by adapter unit tests without Qt, so that TDD remains fast and stable.
23. As a developer, I want the insight package only behind `meekoppel_workflow_v2`, so that we do not maintain two parallel preview UX paths.
24. As a product owner, I want Haarlem validation documented with the v2 flag on for this package, so that production rollout is evidence-based.
25. As a reliability-analist, I want to answer “16 or 63 tasks?”, “why 2047?”, and “which task drives that?” within ten seconds without scrolling, so that the acceptance bar for “insightful enough” is met.

## Implementation Decisions

### Placement in slice 54

- **Issue 03:** selectiedialoog MVP (checkbox, kolommen, apply guard).
- **Issue 03b:** epic preview-inzicht (dit PRD) — opgesplitst in **03c–03g**:
  - **03c** — locatietabel baseline/tooltip (parallel start)
  - **03d** — adapter scope/trekkers/jaarrijen
  - **03e** — dialoog header + jaarkolommen (na 03 + 03d)
  - **03f** — scope-toggle + WYSIWYG apply (na 03e)
  - **03g** — Haarlem handcheck (HITL)
- **Issue 04** (filter/bulk) volgt na **03f**.
- **Blocked by:** slice 54 issues 01–02; slice **55** GO voor 03d+ dialoog-keten; issue **03** voor 03e+.

### Deep modules (testable, Qt-free where possible)

| Module | Responsibility |
|--------|----------------|
| **Meekoppel bundle preview builder** (extend apply/panel adapter) | Resolves `BundleScopeKind` (`location_row` \| `pbs_selection`), task set, baseline/effective/target per row, target drivers, summary lines, sort order (drivers first, then \|Δ\|). |
| **MeekoppelWorkflowService** | Accepts scope parameter; returns enriched preview payload on `WorkflowResult`; apply uses same scope ∩ checked pm_ids. |
| **Meekoppel display service** | Baseline-labelled table headers; tooltip lines `baseline X · effectief Y` when overlay active. |
| **Meekoppel preview dialog (view)** | Header: scope line, scope toggle, “Bepaald door …”, confirmation on apply; table: columns + driver styling. |

No new motor run; effective years reuse existing `effective_due_year` + overlay state.

### Adapter contract (extend preview DTO — grill decision A)

Extend the existing location/bundle preview payload (and `WorkflowResult.preview_payload`) with insight fields. Core shape (decision-rich):

```python
BundleScopeKind = Literal["location_row", "pbs_selection"]

@dataclass(frozen=True)
class MeekoppelTargetDriver:
    pm_id: str
    task_label: str
    baseline_year: int
    effective_year: int

@dataclass(frozen=True)
class MeekoppelPreviewTaskRow:
    pm_id: str
    task_label: str
    baseline_year: int
    effective_year: int
    target_year: int
    delta_years: int          # target - effective
    is_target_driver: bool
    blocked_reason: str | None

# On MeekoppelLocationPreview (or nested bundle_insight):
scope_kind: BundleScopeKind
scope_label: str              # human-readable, e.g. "HWP-IN · 16 REV"
scope_task_count: int
target_drivers: tuple[MeekoppelTargetDriver, ...]
summary_lines: tuple[str, ...]
task_rows: tuple[MeekoppelPreviewTaskRow, ...]  # sorted: drivers, |delta|, label
```

Existing `moves`, `target_year`, `blocked_reason`, `skipped` remain for apply guard compatibility.

### Scope resolution rules

- **Open default (hybrid):** if exactly one locatietabelrij selected → `location_row` with that group’s tasks; else `pbs_selection` with `collect_rev_tasks_for_pbs_selection`.
- **In-dialog toggle:** switch `location_row` ↔ `pbs_selection` with full recompute; checkbox model reset to all shiftable checked + user-visible notice.
- **Anchor:** unchanged (`earlier` \| `later` from paneel); target = min/max of **effective** years over shiftable checked set (same as today’s `preview_meekoppel_rev_tasks`).

### Target driver rules

- After target year computed: drivers = shiftable tasks where `effective_year == target_year`.
- Summary: one driver → name + baseline/effective breakdown; multiple → count + optional list cap in UI with full list in table.

### Locatietabel (A+B, outside dialog)

- Rename/clarify column labels to reference **baseline** (e.g. “Eerste uitvoering (baseline)”, “Verschil (baseline)”).
- Tooltip: per REV `baseline {b} · effectief {e}` only when what-if planning overlay is active; otherwise baseline only.

### Apply contract (A+D)

- Apply mutates overlay only for **checked** pm_ids in **active scope** with paneel anchor.
- Short confirmation string before commit (scope label + count + target year).
- No apply of hidden PBS-wide set when preview scope is location row.

### Feature flag

- Entire insight package only when `meekoppel_workflow_v2` enabled.
- Legacy preview unchanged.

### ADR / architecture alignment

- ADR-0005: overlay-only, preview-before-apply; insight supports informed preview, does not add motor runs.
- UI/kern-decoupling: views call `MeekoppelWorkflowService` only; no `rcm_core` imports in views except typing.

## Testing Decisions

**Good tests** assert observable outcomes via public adapter/workflow APIs: scope kind, task counts, driver identity, year columns, sort order, summary text fragments — not private view widgets.

### Modules under test

- Bundle preview builder / extended `MeekoppelLocationPreview` factory paths (unit).
- `MeekoppelWorkflowService.preview` with `location_row` vs `pbs_selection` (unit).
- Display service: tooltip and header label helpers (unit).
- Optional thin integration: workflow preview → apply WYSIWYG on fixture project (adapter).

### Scenarios (minimum)

1. **HWP-IN scenario:** location row all baseline year 2, span 0; PBS selection includes task with effective 21 → row scope preview target 2 no moves; PBS scope target 21 with named driver(s).
2. **Hybrid default:** one table row selected → `location_row`; none → `pbs_selection`.
3. **Scope toggle:** switch row → PBS resets selection metadata and changes target/drivers.
4. **Driver sort/mark:** driver rows first; `is_target_driver` true only on ties at target effective year.
5. **Tooltip:** with overlay shift, tooltip contains both baseline and effective; without overlay, baseline only.

### Prior art

- `tests/test_meekoppel_apply_service.py` (preview moves, effective year).
- `tests/test_meekoppel_panel_service.py` (scope, groups).
- `tests/test_desktop_meekoppel_workspace.py` (workflow v2 flag routing).

## Out of Scope

- Legacy `QMessageBox` preview parity (insight only in v2 dialog).
- Checkbox/filter/bulk behavior (issue 04).
- Live doeljaar on partial checkbox subset beyond what issue 05 defines (unless already in 03 scope).
- Audit trail / bundel-id notes (issues 06–07).
- Changing discovery span rules or parent-rollup (slice 55).
- Full table columns for effective in locatietabel (only tooltip + header clarity).
- Optional “show only shifting tasks” filter (deferred to issue 04).

## Further Notes

- **Acceptance (human):** analist answers scope, target year rationale, and driver name in ≤10 s on Haarlem-like HWP-IN case with `RCM_MEEKOPPEL_WORKFLOW_V2=1`.
- **Performance:** tooltip effective values only for tasks in visible location rows; truncate long tooltips as today.
- **Risks:** slice 55 Haarlem GO still required for 03+ chain; parent-rollup changes group sizes but not insight semantics.
- **Issue tracker:** epic `issues/03b.md`; implementatie via `issues/03c.md` … `issues/03g.md`.
