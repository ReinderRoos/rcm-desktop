# HILT102 — Handcheck RCM2 presentatielaag v1

**Issues:** slice 102 issues 04 (A), 06 (B1), 08 (B2)  
**Datum:** 2026-06-16  
**Status:** A done (GO); B1 done (GO); B2 done (GO) — **completed**

## Doel

Visuele QA van slice 102 in drie checkpoints: reskin/shell (A), Faalwijze-analyse
tabel (B1), diagram (B2).

## Voorbereiding

1. App: `python -m rcm_desktop.main`
2. Project: `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`

---

## HILT102-A — Reskin / shell (issue 04)

| # | Check | Uitkomst |
|---|-------|----------|
| A1 | Navy topbar + App-wordmark (Delta Pi + RCM2) | ✅ OK (na contrast-fix) |
| A2 | StatusStrip: validatie + MC-status persistent zichtbaar | ✅ OK |
| A3 | Footer: transient melding bij opslaan/export/run voltooid | ⚠️ Known gap — footer-balk zichtbaar; meldingen nog niet wired |
| A4 | KPI-overzicht standaard ingeklapt; open via Beeld | ✅ OK |
| A5 | Delta Pi-thema op Input-grids én Output-views | ✅ OK |
| A6 | Scenario-kleur rood/magenta in Top 10 + LCC + FM compare | ⚠️ OK met kleine accentverschillen |
| A7 | Geen functionele regressie (run, compare toggle, view-switch) | ✅ OK |

**GO/NO-GO A:** **GO** (2026-06-16, ReinderRoos)

### Known gaps v1 (non-blocking)
- A3: `show_workspace_footer_message` nog niet gekoppeld aan opslaan/export/run
- A6: Lichte accentverschillen scenario-kleur tussen compare-views

---

## HILT102-B1 — Faalwijze-analyse tabel (issue 06)

Vereist: scenariovergelijking actief, FM-resultaten view.

| # | Check | Uitkomst |
|---|-------|----------|
| B1.1 | Metric-wissel toont alleen actieve metriek-kolom + id/naam | ✅ OK |
| B1.2 | Rijen uitgelijnd: zelfde faalwijze opzelfde rij S1/S2 | ✅ OK |
| B1.3 | FM alleen in S2: lege cel links, waarde rechts, geen highlight | ⚠️ Niet testbaar — identieke FM-set in beide scenario's (Haarlem demo) |
| B1.4 | >20% verschil (S1>0): highlight op beide kolommen | ✅ OK |
| B1.5 | NMF/RF-toggle default uit; aan = kolommen zichtbaar | ✅ OK |
| B1.6 | FM-inspector niet beschikbaar in compare | ✅ OK |
| B1.7 | Mixed MC/analytisch compare plausibel (post slice 101) | ✅ OK |

**GO/NO-GO B1:** **GO** (2026-06-16, ReinderRoos)

### Known gaps v1 (non-blocking)
- B1.3: Asymmetrische FM-set niet aanwezig in Haarlem demo; gedrag gedekt door adapter-tests

---

## HILT102-B2 — Diagram (issue 08)

| # | Check | Uitkomst |
|---|-------|----------|
| B2.1 | Tabel↔diagram-switch exclusief; default tabel | ✅ OK |
| B2.2 | Diagram: gepaarde balken S1 rood / S2 magenta | ✅ OK |
| B2.3 | Zelfde rijvolgorde als tabel | ✅ OK |
| B2.4 | Highlight op balken waar tabel ook highlight | ✅ OK |
| B2.5 | Metric-wissel herberekent tabel én diagram | ✅ OK |

**GO/NO-GO B2:** **GO** (2026-06-16, ReinderRoos)

---

## Slice-afsluiting

**GO op B2** — PRD status → `done` (2026-06-16).
